from __future__ import annotations

import json
from typing import Iterator

import httpx

from .base import LLMClient, LLMResult


class AnthropicError(RuntimeError):
    pass


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key, base_url, version, model, timeout):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._version = version
        self._model = model
        self._timeout = timeout

    def _headers(self):
        return {
            "x-api-key": self._api_key,
            "anthropic-version": self._version,
            "content-type": "application/json",
        }

    def _payload(self, system, messages, max_tokens, stream):
        return {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "stream": stream,
        }

    def complete(self, system, messages, max_tokens) -> LLMResult:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/v1/messages",
                headers=self._headers(),
                json=self._payload(system, messages, max_tokens, stream=False),
            )
        if response.status_code >= 400:
            raise AnthropicError(f"Anthropic returned status {response.status_code}")
        data = response.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return LLMResult(
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            model=str(data.get("model", self._model)),
        )

    def stream(self, system, messages, max_tokens) -> Iterator[dict]:
        input_tokens = 0
        output_tokens = 0
        text_parts = []
        with httpx.Client(timeout=self._timeout) as client:
            with client.stream(
                "POST",
                f"{self._base_url}/v1/messages",
                headers=self._headers(),
                json=self._payload(system, messages, max_tokens, stream=True),
            ) as response:
                if response.status_code >= 400:
                    raise AnthropicError(f"Anthropic returned status {response.status_code}")
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    event = json.loads(line[len("data:"):].strip())
                    kind = event.get("type")
                    if kind == "message_start":
                        input_tokens = int(
                            event.get("message", {}).get("usage", {}).get("input_tokens", 0)
                        )
                    elif kind == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            chunk = delta.get("text", "")
                            text_parts.append(chunk)
                            yield {"type": "text", "text": chunk}
                    elif kind == "message_delta":
                        output_tokens = int(event.get("usage", {}).get("output_tokens", output_tokens))
        yield {
            "type": "result",
            "result": LLMResult(
                text="".join(text_parts),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=self._model,
            ),
        }
