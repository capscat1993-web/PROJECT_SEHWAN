from django.core.management.base import BaseCommand, CommandError

from reports.services.health_export import export_health_excel


class Command(BaseCommand):
    help = "특정 회사의 재무건전성 평가 엑셀 파일을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument("company_id", type=int)
        parser.add_argument("--output", type=str, default="")

    def handle(self, *args, **options):
        company_id = options["company_id"]
        output = options["output"]
        try:
            buffer, company_name = export_health_excel(company_id)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        filename = output or f"{company_name}_재무건전성평가.xlsx"
        with open(filename, "wb") as handle:
            handle.write(buffer.getvalue())
        self.stdout.write(self.style.SUCCESS(f"saved: {filename}"))
