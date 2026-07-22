import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum

from copilot.models import CopilotUsageLog
from copilot.services.pricing import cost_usd


def build_report():
    rows = (
        CopilotUsageLog.objects.values("feature")
        .annotate(
            calls=Count("id"),
            cache_hits=Count("id", filter=Q(cache_hit=True)),
            input_tokens=Sum("input_tokens"),
            output_tokens=Sum("output_tokens"),
        )
        .order_by("feature")
    )
    report = []
    for row in rows:
        input_tokens = row["input_tokens"] or 0
        output_tokens = row["output_tokens"] or 0
        report.append(
            {
                "feature": row["feature"],
                "calls": row["calls"],
                "cache_hits": row["cache_hits"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost_usd(input_tokens, output_tokens), 6),
            }
        )
    return report


class Command(BaseCommand):
    help = "Summarize logged copilot usage into token counts and reproducible cost."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        report = build_report()
        if options["as_json"]:
            self.stdout.write(json.dumps(report, indent=2))
            return
        self.stdout.write(f"{'feature':<14}{'calls':>7}{'in_tok':>10}{'out_tok':>10}{'cost_usd':>12}")
        for row in report:
            self.stdout.write(
                f"{row['feature']:<14}{row['calls']:>7}{row['input_tokens']:>10}"
                f"{row['output_tokens']:>10}{row['cost_usd']:>12.6f}"
            )
