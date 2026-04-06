from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
import os

from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))


@router.get("/api/companies")
async def list_companies(q: str = Query("", description="검색어")):
    with get_db() as conn:
        if q:
            rows = conn.execute(
                "SELECT id, company_name, representatives, biz_no, report_date, industry, main_product "
                "FROM report_imports WHERE company_name LIKE ? ORDER BY company_name",
                (f"%{q}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, company_name, representatives, biz_no, report_date, industry, main_product "
                "FROM report_imports ORDER BY company_name"
            ).fetchall()
    return [dict(r) for r in rows]


@router.get("/company/{company_id}")
async def company_detail(request: Request, company_id: int):
    return templates.TemplateResponse(request, "company.html", {"company_id": company_id})


@router.get("/api/companies/{company_id}")
async def get_company(company_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, company_name, representatives, biz_no, report_date, industry, main_product "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
    if not row:
        return {"error": "not found"}
    return dict(row)
