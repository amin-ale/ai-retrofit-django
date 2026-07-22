from __future__ import annotations

from typing import Iterator

from .base import LLMClient, LLMResult, estimate_tokens


def _prompt_text(system, messages):
    parts = [system or ""]
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(block.get("text", "") for block in content)
        parts.append(str(content))
    return "\n".join(parts)


class FakeLLMClient(LLMClient):
    def __init__(self, rules=None, default_text="", model="fake-model"):
        self._rules = rules or []
        self._default_text = default_text
        self._model = model
        self.calls = []

    def _resolve(self, system, messages):
        prompt = _prompt_text(system, messages)
        for rule in self._rules:
            needles = rule.get("contains", [])
            if needles and all(needle in prompt for needle in needles):
                return rule, prompt
        return None, prompt

    def _build_result(self, rule, prompt):
        text = rule["text"] if rule else self._default_text
        input_tokens = rule.get("input_tokens") if rule else None
        output_tokens = rule.get("output_tokens") if rule else None
        if input_tokens is None:
            input_tokens = estimate_tokens(prompt)
        if output_tokens is None:
            output_tokens = estimate_tokens(text)
        return LLMResult(text=text, input_tokens=input_tokens, output_tokens=output_tokens, model=self._model)

    def complete(self, system, messages, max_tokens) -> LLMResult:
        rule, prompt = self._resolve(system, messages)
        self.calls.append(prompt)
        return self._build_result(rule, prompt)

    def stream(self, system, messages, max_tokens) -> Iterator[dict]:
        rule, prompt = self._resolve(system, messages)
        self.calls.append(prompt)
        result = self._build_result(rule, prompt)
        for word in result.text.split(" "):
            yield {"type": "text", "text": word + " "}
        yield {"type": "result", "result": result}
