ALLOWED_VIEWS = ("customers", "tickets", "ticket_messages")

VIEW_SOURCES = {
    "customers": (
        "SELECT id, name, email, plan, created_at, tenant_id "
        "FROM helpdesk_customer WHERE tenant_id = {tenant_id}"
    ),
    "tickets": (
        "SELECT id, customer_id, subject, status, priority, created_at, updated_at, tenant_id "
        "FROM helpdesk_ticket WHERE tenant_id = {tenant_id}"
    ),
    "ticket_messages": (
        "SELECT m.id, m.ticket_id, m.author_kind, m.body, m.created_at "
        "FROM helpdesk_ticketmessage m "
        "JOIN helpdesk_ticket t ON m.ticket_id = t.id "
        "WHERE t.tenant_id = {tenant_id}"
    ),
}

SCHEMA_DESCRIPTION = """\
You can query these read-only views. Every view is already scoped to the current tenant.

customers(id, name, email, plan, created_at)
tickets(id, customer_id, subject, status, priority, created_at, updated_at)
  status in ('open','pending','resolved','closed')
  priority in ('low','normal','high','urgent')
ticket_messages(id, ticket_id, author_kind, body, created_at)
  author_kind in ('customer','agent')

tickets.customer_id references customers.id
ticket_messages.ticket_id references tickets.id
"""


def build_view_ddl(tenant_id):
    tenant_id = int(tenant_id)
    return [
        f"CREATE TEMP VIEW {name} AS {source.format(tenant_id=tenant_id)}"
        for name, source in VIEW_SOURCES.items()
    ]
