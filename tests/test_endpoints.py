import json

import pytest
from django.test import Client

from copilot.models import CopilotTenantConfig


@pytest.fixture
def client():
    return Client()


def _post(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def _drain(response):
    return b"".join(response.streaming_content).decode("utf-8")


def test_status_endpoint(client, acme):
    response = client.get("/copilot/status", {"tenant": acme})
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert "remaining_tokens" in body


def test_search_endpoint(client, indexed):
    tenant_id = indexed["acme"].id
    response = _post(client, "/copilot/search", {"tenant": tenant_id, "query": "billing refund"})
    assert response.status_code == 200
    assert response.json()["results"]


def test_ask_endpoint_streams_sql_and_tokens(client, acme):
    response = _post(client, "/copilot/ask", {"tenant": acme, "question": "How many open tickets are there?"})
    assert response.status_code == 200
    assert response["Content-Type"] == "text/event-stream"
    payload = _drain(response)
    assert '"event": "sql"' in payload
    assert '"event": "token"' in payload
    assert '"event": "done"' in payload


def test_ask_endpoint_blocks_dangerous_query(client, acme):
    response = _post(client, "/copilot/ask", {"tenant": acme, "question": "drop the users table"})
    assert response.status_code == 400
    assert "reason" in response.json()


def test_ask_endpoint_budget_429(client, acme):
    CopilotTenantConfig.objects.create(tenant_id=acme, daily_token_budget=0)
    response = _post(client, "/copilot/ask", {"tenant": acme, "question": "How many open tickets are there?"})
    assert response.status_code == 429


def test_ask_endpoint_disabled_404(client, acme):
    CopilotTenantConfig.objects.create(tenant_id=acme, enabled=False)
    response = _post(client, "/copilot/ask", {"tenant": acme, "question": "How many open tickets are there?"})
    assert response.status_code == 404


def test_summarize_endpoint_streams(client, acme):
    from helpdesk.models import Ticket

    ticket = Ticket.objects.get(tenant_id=acme, subject="Export to CSV fails on large accounts")
    response = _post(client, "/copilot/summarize", {"tenant": acme, "ticket_id": ticket.id})
    assert response.status_code == 200
    payload = _drain(response)
    assert '"event": "token"' in payload
    assert '"event": "done"' in payload


def test_missing_params_400(client):
    response = _post(client, "/copilot/search", {"query": "x"})
    assert response.status_code == 400
