from django.core.management.base import BaseCommand

from helpdesk.seeding import seed


class Command(BaseCommand):
    help = "Seed the existing helpdesk product with demo tenants, customers, tickets, and messages."

    def handle(self, *args, **options):
        tenants = seed()
        for slug, tenant in tenants.items():
            self.stdout.write(f"tenant {slug} -> id {tenant.id}")
