import pytest

from copilot.models import CopilotUsageLog
from copilot.services import summarize
from copilot.services.summarize import TicketNotFound


def _ticket(tenant_id, subject):
    from helpdesk.models import Ticket

    return Ticket.objects.get(tenant_id=tenant_id, subject=subject)


def test_summarize_returns_text(acme, fake_llm):
    ticket = _ticket(acme, "Export to CSV fails on large accounts")
    summary = summarize.summarize_ticket(acme, ticket.id, llm=fake_llm)
    assert "export" in summary.lower()


def test_summarize_second_call_hits_cache(acme, fake_llm):
    ticket = _ticket(acme, "Export to CSV fails on large accounts")
    summarize.summarize_ticket(acme, ticket.id, llm=fake_llm)
    summarize.summarize_ticket(acme, ticket.id, llm=fake_llm)
    assert CopilotUsageLog.objects.filter(feature="summary", cache_hit=True).count() == 1


def test_summarize_rejects_other_tenant_ticket(globex, acme, fake_llm):
    ticket = _ticket(acme, "Export to CSV fails on large accounts")
    with pytest.raises(TicketNotFound):
        summarize.summarize_ticket(globex, ticket.id, llm=fake_llm)
