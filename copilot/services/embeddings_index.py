from copilot.models import CopilotEmbedding

from .factory import build_embedding_client


def _ticket_documents(tenant_id):
    from helpdesk.models import Ticket

    tickets = Ticket.objects.filter(tenant_id=tenant_id).prefetch_related("messages")
    documents = []
    for ticket in tickets:
        bodies = " ".join(message.body for message in ticket.messages.all())
        documents.append((ticket.id, f"{ticket.subject}. {bodies}"))
    return documents


def reindex(tenant_id, embedding_client=None):
    client = embedding_client or build_embedding_client()
    documents = _ticket_documents(tenant_id)
    if not documents:
        return 0
    vectors = client.embed([content for _, content in documents])
    for (source_pk, content), vector in zip(documents, vectors):
        CopilotEmbedding.objects.update_or_create(
            source_table="tickets",
            source_pk=source_pk,
            defaults={
                "tenant_id": tenant_id,
                "content": content,
                "vector": vector,
                "model": client.model,
            },
        )
    return len(documents)
