import re

import sqlparse
from sqlparse import tokens as T

from .config import get
from .schema import ALLOWED_VIEWS

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE",
    "TRUNCATE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "MERGE", "INTO", "REINDEX", "ANALYZE",
}

FORBIDDEN_COMPOUND = {"UNION", "EXCEPT", "INTERSECT"}

_FENCE_RE = re.compile(r"```(?:sql)?", re.IGNORECASE)
_TABLE_RE = re.compile(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_.]*)", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)


class SqlGuardError(Exception):
    pass


def _clean(raw):
    text = _FENCE_RE.sub("", raw).strip().strip("`").strip()
    if text.endswith(";"):
        text = text[:-1].strip()
    return text


def _single_statement(sql):
    statements = [s for s in sqlparse.parse(sql) if s.value.strip()]
    if len(statements) != 1:
        raise SqlGuardError("Exactly one statement is allowed")
    return statements[0]


def _reject_comments(sql):
    if "--" in sql or "/*" in sql:
        raise SqlGuardError("Comments are not allowed")


def _reject_keywords(statement):
    words = {
        token.value.upper()
        for token in statement.flatten()
        if token.ttype not in T.Literal.String
    }
    banned = words & FORBIDDEN_KEYWORDS
    if banned:
        raise SqlGuardError(f"Forbidden keyword: {sorted(banned)[0]}")
    compound = words & FORBIDDEN_COMPOUND
    if compound:
        raise SqlGuardError(f"Compound queries are not allowed: {sorted(compound)[0]}")


def _check_tables(sql):
    referenced = {name.lower() for name in _TABLE_RE.findall(sql)}
    if not referenced:
        raise SqlGuardError("Query does not read from any known view")
    disallowed = referenced - set(ALLOWED_VIEWS)
    if disallowed:
        raise SqlGuardError(f"Unknown or disallowed table: {sorted(disallowed)[0]}")


def _enforce_limit(sql):
    max_rows = get("MAX_ROWS")
    match = _LIMIT_RE.search(sql)
    if match is None:
        return f"{sql} LIMIT {max_rows}"
    requested = int(match.group(1))
    if requested > max_rows:
        return _LIMIT_RE.sub(f"LIMIT {max_rows}", sql, count=1)
    return sql


def validate(raw_sql):
    sql = _clean(raw_sql)
    if not sql:
        raise SqlGuardError("Empty query")
    _reject_comments(sql)
    statement = _single_statement(sql)
    if statement.get_type() != "SELECT":
        raise SqlGuardError("Only SELECT statements are allowed")
    _reject_keywords(statement)
    _check_tables(sql)
    return _enforce_limit(sql)
