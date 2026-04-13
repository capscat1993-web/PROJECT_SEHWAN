from django.core.management.base import BaseCommand

from reports.services.company_metadata import enrich_company_metadata


class Command(BaseCommand):
    help = "사업자번호 기준으로 업종 및 주요 제품 메타데이터를 보강합니다."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--workers", type=int, default=4)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"] or None
        workers = max(1, options["workers"])
        force = options["force"]

        updated = enrich_company_metadata(limit=limit, force=force, max_workers=workers)
        if not updated:
            self.stdout.write("updated: 0")
            return

        self.stdout.write(self.style.SUCCESS(f"updated: {len(updated)}"))
        for company_id, payload in sorted(updated.items()):
            self.stdout.write(
                f"[{company_id}] 업종={payload.get('industry', '') or '-'} | 주요제품={payload.get('main_product', '') or '-'}"
            )
