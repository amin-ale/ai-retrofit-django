from __future__ import annotations

import abc
import hashlib
import math
import re

import httpx

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def normalize(vector):
    magnitude = math.sqrt(sum(component * component for component in vector))
    if magnitude == 0:
        return vector
    return [component / magnitude for component in vector]


def cosine_similarity(left, right):
    return sum(a * b for a, b in zip(left, right))


class EmbeddingClient(abc.ABC):
    @property
    @abc.abstractmethod
    def model(self) -> str:
        ...

    @abc.abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class HashingEmbeddingClient(EmbeddingClient):
    def __init__(self, dim=256):
        self._dim = dim

    @property
    def model(self):
        return f"hashing-{self._dim}"

    def _embed_one(self, text):
        vector = [0.0] * self._dim
        for token in _tokenize(text):
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        return normalize(vector)

    def embed(self, texts):
        return [self._embed_one(text) for text in texts]


class VoyageEmbeddingClient(EmbeddingClient):
    def __init__(self, api_key, base_url, model, timeout):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def model(self):
        return self._model

    def embed(self, texts):
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "content-type": "application/json",
                },
                json={"model": self._model, "input": texts},
            )
        response.raise_for_status()
        data = response.json()
        return [normalize(item["embedding"]) for item in data["data"]]
