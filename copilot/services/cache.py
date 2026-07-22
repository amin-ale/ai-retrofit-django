import hashlib

from copilot.llm.base import LLMResult
from copilot.models import CopilotResponseCache


def cache_key(feature, payload):
    digest = hashlib.sha256(f"{feature}\n{payload}".encode("utf-8")).hexdigest()
    return digest


def get_cached(feature, payload):
    key = cache_key(feature, payload)
    row = CopilotResponseCache.objects.filter(cache_key=key).first()
    if row is None:
        return None
    return LLMResult(
        text=row.response_text,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        model="cache",
    )


def put_cached(feature, payload, result):
    key = cache_key(feature, payload)
    CopilotResponseCache.objects.update_or_create(
        cache_key=key,
        defaults={
            "feature": feature,
            "response_text": result.text,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    )
