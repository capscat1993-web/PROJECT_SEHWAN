import urllib.parse
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.financial_health import calculate_health
from app.services.health_export import export_health_excel

router = APIRouter()


def _streaming_health_xlsx(company_id: int) -> StreamingResponse:
    buf, company_name = export_health_excel(company_id)
    filename = urllib.parse.quote(f"{company_name}_재무건전성평가.xlsx")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


# 짧은 별칭(프록시/구버전 라우팅 이슈 회피). UI는 이 경로를 우선 사용.
@router.get("/api/export-health/{company_id}")
async def export_health_alias(company_id: int):
    return _streaming_health_xlsx(company_id)


@router.get("/api/companies/{company_id}/health/export")
async def export_health(company_id: int):
    return _streaming_health_xlsx(company_id)


@router.get("/api/companies/{company_id}/health")
async def get_health(company_id: int):
    return calculate_health(company_id)
