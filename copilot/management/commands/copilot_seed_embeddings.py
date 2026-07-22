from django.core.management.base import BaseCommand

from copilot.services.embeddings_index import reindex
from helpdesk.models import Tenant


class Command(BaseCommand):
    help = "Build semantic-search embeddings for every tenant's tickets."

    def handle(self, *args, **options):
        for tenant in Tenant.objects.all():
            count = reindex(tenant.id)
            self.stdout.write(f"tenant {tenant.slug} -> indexed {count} tickets")
