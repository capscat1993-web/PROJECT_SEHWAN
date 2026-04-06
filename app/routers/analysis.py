from fastapi import APIRouter
from app.services.financial_health import calculate_health

router = APIRouter()


@router.get("/api/companies/{company_id}/health")
async def get_health(company_id: int):
    return calculate_health(company_id)
