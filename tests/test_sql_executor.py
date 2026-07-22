import pytest
from django.db.utils import OperationalError

from copilot.services.sql_executor import execute_scoped


def test_scopes_rows_to_tenant(acme, globex):
    _, acme_rows = execute_scoped("SELECT COUNT(*) FROM tickets", acme)
    _, globex_rows = execute_scoped("SELECT COUNT(*) FROM tickets", globex)
    assert acme_rows[0][0] == 4
    assert globex_rows[0][0] == 2


def test_customers_view_is_tenant_scoped(acme, globex):
    _, acme_rows = execute_scoped("SELECT COUNT(*) FROM customers", acme)
    _, globex_rows = execute_scoped("SELECT COUNT(*) FROM customers", globex)
    assert acme_rows[0][0] == 3
    assert globex_rows[0][0] == 2


def test_ticket_messages_view_joins_within_tenant(acme):
    columns, rows = execute_scoped("SELECT ticket_id, author_kind, body FROM ticket_messages", acme)
    assert columns == ["ticket_id", "author_kind", "body"]
    assert len(rows) > 0


def test_engine_level_read_only_blocks_writes(acme):
    with pytest.raises(OperationalError):
        execute_scoped("CREATE TABLE evil (x INTEGER)", acme)


def test_read_only_pragma_is_restored_after_query(acme):
    execute_scoped("SELECT COUNT(*) FROM tickets", acme)
    from copilot.models import CopilotResponseCache

    CopilotResponseCache.objects.create(cache_key="probe", feature="x", response_text="ok")
    assert CopilotResponseCache.objects.filter(cache_key="probe").exists()
