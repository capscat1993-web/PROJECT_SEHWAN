import urllib.parse
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.financial_health import calculate_health
from app.services.health_export import export_health_excel

router = APIRouter()


@router.get("/api/companies/{company_id}/health")
async def get_health(company_id: int):
    return calculate_health(company_id)


@router.get("/api/companies/{company_id}/health/export")
async def export_health(company_id: int):
    buf, company_name = export_health_excel(company_id)
    filename = urllib.parse.quote(f"{company_name}_재무건전성평가.xlsx")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
