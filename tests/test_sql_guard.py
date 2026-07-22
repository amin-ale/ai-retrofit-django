import pytest

from copilot.services.sql_guard import SqlGuardError, validate


def test_allows_plain_select():
    result = validate("SELECT id, subject FROM tickets WHERE status = 'open'")
    assert result.startswith("SELECT")
    assert "LIMIT" in result.upper()


def test_injects_missing_limit():
    result = validate("SELECT id FROM tickets")
    assert result.upper().endswith("LIMIT 100")


def test_clamps_oversized_limit():
    result = validate("SELECT id FROM tickets LIMIT 100000")
    assert "LIMIT 100" in result
    assert "100000" not in result


def test_strips_code_fence():
    result = validate("```sql\nSELECT id FROM tickets\n```")
    assert result.startswith("SELECT")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE auth_user",
        "DELETE FROM tickets WHERE 1=1",
        "UPDATE tickets SET status = 'closed'",
        "INSERT INTO tickets (subject) VALUES ('x')",
        "SELECT id FROM tickets; DROP TABLE tickets",
        "SELECT * FROM auth_user",
        "SELECT username, password FROM auth_user",
        "SELECT id FROM helpdesk_ticket",
        "SELECT id FROM tickets -- comment",
        "SELECT id FROM tickets UNION SELECT id FROM customers",
        "PRAGMA table_info(tickets)",
        "SELECT id FROM sqlite_master",
    ],
)
def test_rejects_dangerous_sql(sql):
    with pytest.raises(SqlGuardError):
        validate(sql)


def test_allows_forbidden_keyword_inside_string_literal():
    result = validate("SELECT id, subject FROM tickets WHERE subject = 'please DROP everything'")
    assert result.startswith("SELECT")
    assert "LIMIT" in result.upper()


def test_allows_compound_keyword_inside_string_literal():
    result = validate("SELECT id FROM tickets WHERE subject = 'union of workers'")
    assert result.startswith("SELECT")
    assert "LIMIT" in result.upper()
