from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Iterator


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, system: str, messages: list[dict], max_tokens: int) -> LLMResult:
        ...

    @abc.abstractmethod
    def stream(self, system: str, messages: list[dict], max_tokens: int) -> Iterator[dict]:
        ...


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
