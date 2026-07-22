import pytest
from django.test import override_settings

from copilot.models import CopilotTenantConfig
from copilot.services.flags import FeatureDisabled, is_enabled, require_enabled


def test_enabled_by_default(acme):
    assert is_enabled(acme) is True


def test_disabled_per_tenant(acme):
    CopilotTenantConfig.objects.create(tenant_id=acme, enabled=False)
    assert is_enabled(acme) is False
    with pytest.raises(FeatureDisabled):
        require_enabled(acme)


def test_global_kill_switch(acme):
    with override_settings(COPILOT={**_settings(), "ENABLED": False}):
        assert is_enabled(acme) is False


def _settings():
    from django.conf import settings

    return settings.COPILOT
