import pytest

from copilot.models import CopilotTenantConfig
from copilot.services import ask_data
from copilot.services.budget import BudgetExceeded, remaining_tokens, tokens_used_today


def test_zero_budget_blocks_immediately(acme, fake_llm):
    CopilotTenantConfig.objects.create(tenant_id=acme, daily_token_budget=0)
    with pytest.raises(BudgetExceeded):
        ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)


def test_budget_exhausts_after_usage(acme, fake_llm):
    CopilotTenantConfig.objects.create(tenant_id=acme, daily_token_budget=50)
    ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    assert tokens_used_today(acme) > 0
    with pytest.raises(BudgetExceeded):
        ask_data.run_ask(acme, "List the high priority tickets", llm=fake_llm)


def test_budget_is_per_tenant(acme, globex, fake_llm):
    CopilotTenantConfig.objects.create(tenant_id=acme, daily_token_budget=0)
    with pytest.raises(BudgetExceeded):
        ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    result = ask_data.run_ask(globex, "How many open tickets are there?", llm=fake_llm)
    assert result["sql"]
    assert remaining_tokens(globex) >= 0
