from fastapi import APIRouter
from app.database import get_db

router = APIRouter()

# 섹션별 핵심 지표 키워드 매핑
KEY_METRICS = {
    "매출액": ["매출액"],
    "영업이익": ["영업이익（손실）", "영업이익(손실)", "영업이익"],
    "당기순이익": ["당기순이익(손실)", "당기순이익（손실）", "당기순이익"],
}

INCOME_SECTIONS = ["손익계산서", "포괄손익계산서"]


@router.get("/api/companies/{company_id}/sections")
async def get_sections(company_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT section FROM report_values WHERE import_id = ? ORDER BY section",
            (company_id,),
        ).fetchall()
    return [r["section"] for r in rows]


@router.get("/api/companies/{company_id}/financial")
async def get_financial(company_id: int, section: str = ""):
    with get_db() as conn:
        if section:
            rows = conn.execute(
                "SELECT metric, period, value_raw, value_num, unit, submetric, category "
                "FROM report_values WHERE import_id = ? AND section = ? "
                "ORDER BY row_no",
                (company_id, section),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT section, metric, period, value_raw, value_num, unit, submetric, category "
                "FROM report_values WHERE import_id = ? "
                "ORDER BY section, row_no",
                (company_id,),
            ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/companies/{company_id}/periods")
async def get_periods(company_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND period != '-' ORDER BY period",
            (company_id,),
        ).fetchall()
    return [r["period"] for r in rows]


@router.get("/api/companies/{company_id}/financial_table")
async def get_financial_table(company_id: int, section: str = "재무상태표"):
    """Pivot table: metric x period."""
    with get_db() as conn:
        periods = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND section = ? AND period != '-' ORDER BY period",
            (company_id, section),
        ).fetchall()
        period_list = [r["period"] for r in periods]

        rows = conn.execute(
            "SELECT metric, period, value_raw, value_num, category "
            "FROM report_values "
            "WHERE import_id = ? AND section = ? AND submetric IS NULL AND category IS NULL "
            "ORDER BY row_no",
            (company_id, section),
        ).fetchall()

        # category IS NULL 결과가 없으면 category 포함해서 재조회 (예: 현금흐름지표)
        if not rows:
            rows = conn.execute(
                "SELECT metric, period, value_raw, value_num, category "
                "FROM report_values "
                "WHERE import_id = ? AND section = ? AND submetric IS NULL "
                "ORDER BY row_no",
                (company_id, section),
            ).fetchall()

        unit_row = conn.execute(
            "SELECT unit FROM report_values WHERE import_id = ? AND section = ? AND unit IS NOT NULL LIMIT 1",
            (company_id, section),
        ).fetchone()

    unit = unit_row["unit"] if unit_row else ""

    # Build pivot: metric(+category) -> {period: value}
    seen_metrics = []
    pivot = {}
    for r in rows:
        cat = r["category"]
        m = f"{r['metric']} ({cat})" if cat else r["metric"]
        if m not in pivot:
            pivot[m] = {}
            seen_metrics.append(m)
        pivot[m][r["period"]] = {
            "raw": r["value_raw"],
            "num": r["value_num"],
        }

    table = []
    for m in seen_metrics:
        row = {"metric": m, "values": {}}
        for p in period_list:
            row["values"][p] = pivot[m].get(p, {"raw": "", "num": None})
        table.append(row)

    return {"periods": period_list, "rows": table, "unit": unit}


@router.get("/api/companies/{company_id}/key_metrics")
async def get_key_metrics(company_id: int):
    """매출액/영업이익/당기순이익 연도별 시계열 데이터."""
    with get_db() as conn:
        # 손익 섹션에서 데이터 조회
        rows = conn.execute(
            "SELECT metric, period, value_num, value_raw, unit "
            "FROM report_values "
            "WHERE import_id = ? AND section IN ('손익계산서','포괄손익계산서') "
            "AND submetric IS NULL AND category IS NULL AND period != '-' "
            "ORDER BY period",
            (company_id,),
        ).fetchall()

        # unit 파악
        unit_row = conn.execute(
            "SELECT unit FROM report_values "
            "WHERE import_id = ? AND section IN ('손익계산서','포괄손익계산서') AND unit IS NOT NULL LIMIT 1",
            (company_id,),
        ).fetchone()

    unit = unit_row["unit"] if unit_row else ""

    # period 목록 (정렬)
    periods = sorted({r["period"] for r in rows})

    result = {}
    for label, keywords in KEY_METRICS.items():
        series = {}
        for r in rows:
            for kw in keywords:
                if kw in r["metric"]:
                    p = r["period"]
                    if p not in series:
                        series[p] = r["value_num"]
                    break
        result[label] = {p: series.get(p) for p in periods}

    return {"periods": periods, "metrics": result, "unit": unit}


@router.get("/api/companies/{company_id}/income_chart")
async def get_income_chart(company_id: int):
    """손익계산서 전체 지표를 기간별로 반환 (차트 + 표 겸용)."""
    with get_db() as conn:
        # 사용 가능한 손익 섹션 확인
        sections = conn.execute(
            "SELECT DISTINCT section FROM report_values "
            "WHERE import_id = ? AND section IN ('손익계산서','포괄손익계산서') ORDER BY section",
            (company_id,),
        ).fetchall()
        section_list = [r["section"] for r in sections]
        if not section_list:
            return {"periods": [], "rows": [], "unit": "", "sections": []}

        section = section_list[0]

        periods = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND section = ? AND period != '-' ORDER BY period",
            (company_id, section),
        ).fetchall()
        period_list = [r["period"] for r in periods]

        rows = conn.execute(
            "SELECT metric, period, value_raw, value_num, unit "
            "FROM report_values "
            "WHERE import_id = ? AND section = ? AND submetric IS NULL AND category IS NULL "
            "ORDER BY row_no",
            (company_id, section),
        ).fetchall()

        unit_row = conn.execute(
            "SELECT unit FROM report_values WHERE import_id = ? AND section = ? AND unit IS NOT NULL LIMIT 1",
            (company_id, section),
        ).fetchone()

    unit = unit_row["unit"] if unit_row else ""
    seen_metrics = []
    pivot = {}
    for r in rows:
        m = r["metric"]
        if m not in pivot:
            pivot[m] = {}
            seen_metrics.append(m)
        pivot[m][r["period"]] = {"raw": r["value_raw"], "num": r["value_num"]}

    table = []
    for m in seen_metrics:
        row = {"metric": m, "values": {}}
        for p in period_list:
            row["values"][p] = pivot[m].get(p, {"raw": "", "num": None})
        table.append(row)

    return {"periods": period_list, "rows": table, "unit": unit, "sections": section_list}
