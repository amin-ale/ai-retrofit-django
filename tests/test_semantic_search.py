from copilot.services.semantic_search import search


def test_search_finds_relevant_ticket(indexed):
    tenant_id = indexed["acme"].id
    results = search(tenant_id, "duplicate billing charge refund")
    assert results
    top = results[0]
    assert "billing" in top["content"].lower() or "charged" in top["content"].lower()


def test_search_is_tenant_scoped(indexed):
    acme_id = indexed["acme"].id
    globex_id = indexed["globex"].id
    acme_pks = {row["source_pk"] for row in search(acme_id, "export csv timeout")}
    globex_pks = {row["source_pk"] for row in search(globex_id, "export csv timeout")}
    assert acme_pks.isdisjoint(globex_pks)


def test_search_respects_top_k(indexed):
    tenant_id = indexed["acme"].id
    results = search(tenant_id, "anything", top_k=2)
    assert len(results) <= 2
