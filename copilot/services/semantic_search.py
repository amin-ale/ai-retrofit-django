from copilot.models import CopilotEmbedding

from .config import get
from .factory import build_embedding_client
from .flags import require_enabled
from .llm_embed_util import top_matches


def search(tenant_id, query, top_k=None, embedding_client=None):
    require_enabled(tenant_id)
    client = embedding_client or build_embedding_client()
    limit = top_k or get("SEARCH_TOP_K")
    query_vector = client.embed([query])[0]
    stored = list(
        CopilotEmbedding.objects.filter(tenant_id=tenant_id).values(
            "source_table", "source_pk", "content", "vector"
        )
    )
    ranked = top_matches(query_vector, stored, limit)
    return [
        {
            "source_table": item["source_table"],
            "source_pk": item["source_pk"],
            "content": item["content"],
            "score": round(score, 6),
        }
        for score, item in ranked
    ]
