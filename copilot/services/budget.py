from django.db.models import Sum
from django.utils import timezone

from copilot.models import CopilotTenantConfig, CopilotUsageLog

from .config import get


class BudgetExceeded(Exception):
    def __init__(self, used, limit):
        self.used = used
        self.limit = limit
        super().__init__(f"Daily token budget reached ({used}/{limit})")


def daily_budget(tenant_id):
    config = CopilotTenantConfig.objects.filter(tenant_id=tenant_id).first()
    if config is not None and config.daily_token_budget is not None:
        return config.daily_token_budget
    return get("DAILY_TOKEN_BUDGET")


def tokens_used_today(tenant_id):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    aggregate = (
        CopilotUsageLog.objects.filter(tenant_id=tenant_id, created_at__gte=start, cache_hit=False)
        .aggregate(total=Sum("input_tokens") + Sum("output_tokens"))
    )
    return aggregate["total"] or 0


def remaining_tokens(tenant_id):
    return max(0, daily_budget(tenant_id) - tokens_used_today(tenant_id))


def require_budget(tenant_id):
    used = tokens_used_today(tenant_id)
    limit = daily_budget(tenant_id)
    if used >= limit:
        raise BudgetExceeded(used, limit)
