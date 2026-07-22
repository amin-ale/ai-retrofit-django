import pytest

from tests.support import make_fake


@pytest.fixture
def fake_llm():
    return make_fake()


@pytest.fixture
def seeded(db):
    from helpdesk.seeding import seed

    return seed()


@pytest.fixture
def acme(seeded):
    return seeded["acme"].id


@pytest.fixture
def globex(seeded):
    return seeded["globex"].id


@pytest.fixture
def indexed(seeded):
    from copilot.services.embeddings_index import reindex

    for tenant in seeded.values():
        reindex(tenant.id)
    return seeded
