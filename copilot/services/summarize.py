from copilot.llm.base import LLMResult

from . import cache, prompts
from .budget import require_budget
from .factory import build_llm_client
from .flags import require_enabled
from .redaction import redact
from .usage import log_usage


class TicketNotFound(Exception):
    pass


def _load_thread(tenant_id, ticket_id):
    from helpdesk.models import Ticket

    ticket = Ticket.objects.filter(tenant_id=tenant_id, id=ticket_id).first()
    if ticket is None:
        raise TicketNotFound(f"Ticket {ticket_id} not found for tenant {tenant_id}")
    lines = [f"Subject: {ticket.subject}"]
    for message in ticket.messages.all():
        lines.append(f"{message.author_kind}: {message.body}")
    return "\n".join(lines)


def _prepare(tenant_id, ticket_id):
    require_enabled(tenant_id)
    require_budget(tenant_id)
    thread = _load_thread(tenant_id, ticket_id)
    return redact(thread)


def summarize_ticket(tenant_id, ticket_id, user_id=None, llm=None):
    client = llm or build_llm_client()
    redacted_thread = _prepare(tenant_id, ticket_id)
    cached = cache.get_cached("summary", redacted_thread)
    if cached is not None:
        log_usage(tenant_id, user_id, "summary", cached, cache_hit=True)
        return cached.text
    result = client.complete(prompts.SUMMARY_SYSTEM, prompts.summary_messages(redacted_thread), max_tokens=512)
    cache.put_cached("summary", redacted_thread, result)
    log_usage(tenant_id, user_id, "summary", result, cache_hit=False)
    return result.text


def prepare_summary(tenant_id, ticket_id, user_id=None, llm=None):
    client = llm or build_llm_client()
    redacted_thread = _prepare(tenant_id, ticket_id)
    return {
        "client": client,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "thread": redacted_thread,
    }


def stream_from_prep(prep):
    result = None
    for chunk in prep["client"].stream(
        prompts.SUMMARY_SYSTEM, prompts.summary_messages(prep["thread"]), max_tokens=512
    ):
        if chunk["type"] == "text":
            yield {"event": "token", "text": chunk["text"]}
        elif chunk["type"] == "result":
            result = chunk["result"]
    if result is None:
        result = LLMResult(text="", input_tokens=0, output_tokens=0, model="stream")
    cache.put_cached("summary", prep["thread"], result)
    log_usage(prep["tenant_id"], prep["user_id"], "summary", result, cache_hit=False)
    yield {"event": "done"}


def stream_summary(tenant_id, ticket_id, user_id=None, llm=None):
    prep = prepare_summary(tenant_id, ticket_id, user_id, llm)
    yield from stream_from_prep(prep)
