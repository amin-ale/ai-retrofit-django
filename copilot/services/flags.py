from copilot.models import CopilotTenantConfig

from .config import get


class FeatureDisabled(Exception):
    pass


def is_enabled(tenant_id):
    if not get("ENABLED"):
        return False
    config = CopilotTenantConfig.objects.filter(tenant_id=tenant_id).first()
    if config is None:
        return True
    return config.enabled


def require_enabled(tenant_id):
    if not is_enabled(tenant_id):
        raise FeatureDisabled("Copilot is not enabled for this tenant")
