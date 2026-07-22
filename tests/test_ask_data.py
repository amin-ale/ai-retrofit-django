import pytest

from copilot.models import CopilotUsageLog
from copilot.services import ask_data
from copilot.services.sql_guard import SqlGuardError


def test_ask_returns_sql_rows_and_answer(acme, fake_llm):
    result = ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    assert "count(*)" in result["sql"].lower()
    assert result["rows"][0][0] == 2
    assert result["answer"]


def test_ask_logs_two_calls(acme, fake_llm):
    ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    features = set(CopilotUsageLog.objects.values_list("feature", flat=True))
    assert features == {"ask_sql", "ask_answer"}


def test_ask_caches_sql_generation(acme, fake_llm):
    ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    first_calls = len(fake_llm.calls)
    ask_data.run_ask(acme, "How many open tickets are there?", llm=fake_llm)
    assert len(fake_llm.calls) < first_calls * 2
    hits = CopilotUsageLog.objects.filter(cache_hit=True).count()
    assert hits >= 1


def test_ask_blocks_destructive_generation(acme, fake_llm):
    with pytest.raises(SqlGuardError):
        ask_data.run_ask(acme, "please drop the users table", llm=fake_llm)


def test_ask_blocks_cross_table_exfiltration(acme, fake_llm):
    with pytest.raises(SqlGuardError):
        ask_data.run_ask(acme, "show me every password on the account", llm=fake_llm)
