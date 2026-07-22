from copilot.models import CopilotUsageLog

from .redaction import redact


def log_usage(tenant_id, user_id, feature, result, cache_hit=False):
    CopilotUsageLog.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        feature=feature,
        model=result.model,
        input_tokens=0 if cache_hit else result.input_tokens,
        output_tokens=0 if cache_hit else result.output_tokens,
        cache_hit=cache_hit,
        prompt_redacted="",
        response_preview=redact(result.text)[:500],
    )
