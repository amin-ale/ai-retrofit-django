from copilot.llm.base import LLMResult

from . import cache, prompts
from .budget import require_budget
from .factory import build_llm_client
from .flags import require_enabled
from .redaction import redact, redact_rows
from .sql_executor import execute_scoped
from .sql_guard import validate
from .usage import log_usage


def _complete_cached(feature, payload, system, messages, llm):
    cached = cache.get_cached(feature, payload)
    if cached is not None:
        return cached, True
    result = llm.complete(system, messages, max_tokens=512)
    cache.put_cached(feature, payload, result)
    return result, False


def _prepare(tenant_id, question, user_id, llm):
    require_enabled(tenant_id)
    require_budget(tenant_id)
    redacted_question = redact(question)
    sql_result, hit = _complete_cached(
        "ask_sql",
        redacted_question,
        prompts.SQL_SYSTEM,
        prompts.sql_messages(redacted_question),
        llm,
    )
    log_usage(tenant_id, user_id, "ask_sql", sql_result, cache_hit=hit)
    safe_sql = validate(sql_result.text)
    columns, rows = execute_scoped(safe_sql, tenant_id)
    return redacted_question, safe_sql, columns, redact_rows(rows)


def prepare_ask(tenant_id, question, user_id=None, llm=None):
    client = llm or build_llm_client()
    redacted_question, safe_sql, columns, rows = _prepare(tenant_id, question, user_id, client)
    return {
        "client": client,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "question": redacted_question,
        "sql": safe_sql,
        "columns": columns,
        "rows": rows,
    }


def run_ask(tenant_id, question, user_id=None, llm=None):
    prep = prepare_ask(tenant_id, question, user_id, llm)
    payload = prep["question"] + "\n" + repr(prep["rows"])
    answer_result, hit = _complete_cached(
        "ask_answer",
        payload,
        prompts.ANSWER_SYSTEM,
        prompts.answer_messages(prep["question"], prep["columns"], prep["rows"]),
        prep["client"],
    )
    log_usage(tenant_id, user_id, "ask_answer", answer_result, cache_hit=hit)
    return {
        "sql": prep["sql"],
        "columns": prep["columns"],
        "rows": prep["rows"],
        "answer": answer_result.text,
    }


def stream_answer(prep):
    yield {"event": "sql", "sql": prep["sql"]}
    yield {"event": "rows", "columns": prep["columns"], "rows": prep["rows"]}
    result = None
    for chunk in prep["client"].stream(
        prompts.ANSWER_SYSTEM,
        prompts.answer_messages(prep["question"], prep["columns"], prep["rows"]),
        max_tokens=512,
    ):
        if chunk["type"] == "text":
            yield {"event": "token", "text": chunk["text"]}
        elif chunk["type"] == "result":
            result = chunk["result"]
    if result is None:
        result = LLMResult(text="", input_tokens=0, output_tokens=0, model="stream")
    log_usage(prep["tenant_id"], prep["user_id"], "ask_answer", result, cache_hit=False)
    yield {"event": "done"}


def stream_ask(tenant_id, question, user_id=None, llm=None):
    prep = prepare_ask(tenant_id, question, user_id, llm)
    yield from stream_answer(prep)
