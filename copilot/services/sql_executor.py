from django.db import connection

from .config import get
from .schema import ALLOWED_VIEWS, build_view_ddl


def execute_scoped(sql, tenant_id):
    max_rows = get("MAX_ROWS")
    with connection.cursor() as cursor:
        try:
            for statement in build_view_ddl(tenant_id):
                cursor.execute(statement)
            cursor.execute("PRAGMA query_only = ON")
            cursor.execute(sql)
            columns = [description[0] for description in cursor.description]
            rows = [list(row) for row in cursor.fetchmany(max_rows)]
        finally:
            cursor.execute("PRAGMA query_only = OFF")
            for name in ALLOWED_VIEWS:
                cursor.execute(f"DROP VIEW IF EXISTS {name}")
    return columns, rows
