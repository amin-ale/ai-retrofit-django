from .schema import SCHEMA_DESCRIPTION

SQL_SYSTEM = (
    "You convert a helpdesk analyst's question into a single read-only SQLite SELECT.\n"
    "Rules: SELECT only; reference only the listed views; no writes, DDL, comments, "
    "semicolons, or UNION; always include a LIMIT clause. Return only the SQL.\n\n"
    + SCHEMA_DESCRIPTION
)

ANSWER_SYSTEM = (
    "You are a helpdesk analyst. Given a question and the rows a SQL query returned, "
    "write a concise answer of one to three sentences. Use only the rows provided; "
    "do not invent data."
)

SUMMARY_SYSTEM = (
    "Summarize this support ticket thread in two to four sentences for an agent "
    "picking it up. Note the customer's problem, what has been tried, and the current state."
)


def sql_messages(question):
    return [{"role": "user", "content": f"Question: {question}\nSQL:"}]


def answer_messages(question, columns, rows):
    body = "\n".join(", ".join(str(value) for value in row) for row in rows[:20])
    return [
        {
            "role": "user",
            "content": (
                "Summarize these query results.\n"
                f"Question: {question}\n"
                f"Columns: {', '.join(columns)}\n"
                f"Rows:\n{body}\n"
                "Answer:"
            ),
        }
    ]


def summary_messages(thread):
    return [{"role": "user", "content": thread}]
