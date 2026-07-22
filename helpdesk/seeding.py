from helpdesk.models import Customer, Ticket, TicketMessage, Tenant

_TENANTS = [
    {
        "slug": "acme",
        "name": "Acme Support",
        "customers": [
            {"name": "Dana Reed", "email": "dana@acme-customer.test", "plan": "pro"},
            {"name": "Omar Farouk", "email": "omar@acme-customer.test", "plan": "free"},
            {"name": "Priya Nair", "email": "priya@acme-customer.test", "plan": "pro"},
        ],
        "tickets": [
            {
                "customer": 0,
                "subject": "Export to CSV fails on large accounts",
                "status": "open",
                "priority": "high",
                "messages": [
                    ("customer", "Exporting our 40k-row report just spins forever and never downloads."),
                    ("agent", "Thanks Dana, reproduced it on staging. Looks like a timeout on the export worker."),
                    ("customer", "Any workaround? We need the numbers for a board meeting tomorrow."),
                ],
            },
            {
                "customer": 1,
                "subject": "Reset password email never arrives",
                "status": "pending",
                "priority": "normal",
                "messages": [
                    ("customer", "I requested a password reset three times and nothing shows up, not even in spam."),
                    ("agent", "Our logs show the mail bounced. Can you confirm the address on file is current?"),
                ],
            },
            {
                "customer": 2,
                "subject": "Billing charged twice this month",
                "status": "open",
                "priority": "urgent",
                "messages": [
                    ("customer", "We were charged the plan fee twice on the 3rd. Please refund the duplicate."),
                    ("agent", "Confirmed a duplicate charge, refund initiated. It clears in 5-7 business days."),
                ],
            },
            {
                "customer": 0,
                "subject": "Feature request: dark mode",
                "status": "resolved",
                "priority": "low",
                "messages": [
                    ("customer", "Would love a dark theme for late-night shifts."),
                    ("agent", "Shipped in this week's release under Settings > Appearance."),
                ],
            },
        ],
    },
    {
        "slug": "globex",
        "name": "Globex Helpdesk",
        "customers": [
            {"name": "Lena Ortiz", "email": "lena@globex-customer.test", "plan": "pro"},
            {"name": "Sam Cho", "email": "sam@globex-customer.test", "plan": "free"},
        ],
        "tickets": [
            {
                "customer": 0,
                "subject": "API rate limits too aggressive",
                "status": "open",
                "priority": "high",
                "messages": [
                    ("customer", "We hit 429s at 20 req/s but the docs promise 50. What is the real limit?"),
                    ("agent", "The documented 50 is per-account; you may be sharing a key. Checking your plan."),
                ],
            },
            {
                "customer": 1,
                "subject": "Onboarding wizard skips step 2",
                "status": "closed",
                "priority": "normal",
                "messages": [
                    ("customer", "New teammates never see the permissions step during onboarding."),
                    ("agent", "Fixed a redirect bug that skipped step 2. Please re-invite the affected users."),
                ],
            },
        ],
    },
]


def seed():
    tenants = {}
    for spec in _TENANTS:
        tenant, _ = Tenant.objects.get_or_create(slug=spec["slug"], defaults={"name": spec["name"]})
        tenants[spec["slug"]] = tenant
        customers = []
        for customer_spec in spec["customers"]:
            customer, _ = Customer.objects.get_or_create(
                tenant=tenant,
                email=customer_spec["email"],
                defaults={"name": customer_spec["name"], "plan": customer_spec["plan"]},
            )
            customers.append(customer)
        for ticket_spec in spec["tickets"]:
            ticket, created = Ticket.objects.get_or_create(
                tenant=tenant,
                customer=customers[ticket_spec["customer"]],
                subject=ticket_spec["subject"],
                defaults={"status": ticket_spec["status"], "priority": ticket_spec["priority"]},
            )
            if created:
                for author_kind, body in ticket_spec["messages"]:
                    TicketMessage.objects.create(ticket=ticket, author_kind=author_kind, body=body)
    return tenants
