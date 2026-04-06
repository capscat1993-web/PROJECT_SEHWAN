"""재무건전성 지표 계산 서비스."""

from typing import Dict, List, Optional, Tuple
from app.database import get_db


def _find_value(rows: list, metric_keywords: List[str], period: str) -> Optional[float]:
    """Find a value by matching metric name containing any of the keywords."""
    for r in rows:
        if r["period"] != period:
            continue
        name = r["metric"].replace(" ", "")
        for kw in metric_keywords:
            if kw in name:
                return r["value_num"]
    return None


def calculate_health(company_id: int) -> Dict:
    """Calculate financial health ratios for the latest period."""
    with get_db() as conn:
        # Get latest period
        period_row = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND period != '-' ORDER BY period DESC LIMIT 1",
            (company_id,),
        ).fetchone()
        if not period_row:
            return {"error": "데이터 없음", "ratios": {}, "period": ""}

        latest_period = period_row["period"]

        bs_rows = conn.execute(
            "SELECT metric, period, value_num FROM report_values "
            "WHERE import_id = ? AND section = '재무상태표' AND submetric IS NULL",
            (company_id,),
        ).fetchall()

        is_rows = conn.execute(
            "SELECT metric, period, value_num FROM report_values "
            "WHERE import_id = ? AND section IN ('손익계산서', '포괄손익계산서') AND submetric IS NULL",
            (company_id,),
        ).fetchall()

    # Extract key values
    current_assets = _find_value(bs_rows, ["유동자산"], latest_period)
    current_liabilities = _find_value(bs_rows, ["유동부채"], latest_period)
    total_liabilities = _find_value(bs_rows, ["부채총계", "부채합계"], latest_period)
    total_equity = _find_value(bs_rows, ["자본총계", "자본합계"], latest_period)
    inventory = _find_value(bs_rows, ["재고자산"], latest_period)
    retained_earnings = _find_value(bs_rows, ["이익잉여금"], latest_period)
    paid_in_capital = _find_value(bs_rows, ["자본금"], latest_period)
    operating_income = _find_value(is_rows, ["영업이익", "영업손익"], latest_period)
    interest_expense = _find_value(is_rows, ["이자비용", "금융비용"], latest_period)

    ratios = {}

    # 유동비율 (Current Ratio)
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios["유동비율"] = round(current_assets / current_liabilities * 100, 1)

    # 부채비율 (Debt Ratio)
    if total_liabilities is not None and total_equity and total_equity != 0:
        ratios["부채비율"] = round(total_liabilities / total_equity * 100, 1)

    # 당좌비율 (Quick Ratio)
    if current_assets is not None and current_liabilities and current_liabilities != 0:
        inv = inventory or 0
        ratios["당좌비율"] = round((current_assets - inv) / current_liabilities * 100, 1)

    # 유보율 (Retained Earnings Ratio)
    if retained_earnings is not None and paid_in_capital and paid_in_capital != 0:
        ratios["유보율"] = round(retained_earnings / paid_in_capital * 100, 1)

    # 이자보상비율 (Interest Coverage Ratio)
    if operating_income is not None and interest_expense and interest_expense != 0:
        ratios["이자보상비율"] = round(operating_income / interest_expense, 2)

    # Score each ratio (0-100)
    scores = {}
    if "유동비율" in ratios:
        v = ratios["유동비율"]
        scores["유동비율"] = min(100, max(0, v / 2))  # 200% = 100점
    if "부채비율" in ratios:
        v = ratios["부채비율"]
        scores["부채비율"] = min(100, max(0, 100 - v / 2))  # 0% = 100점, 200% = 0점
    if "당좌비율" in ratios:
        v = ratios["당좌비율"]
        scores["당좌비율"] = min(100, max(0, v / 1.5))  # 150% = 100점
    if "유보율" in ratios:
        v = ratios["유보율"]
        scores["유보율"] = min(100, max(0, v / 10))  # 1000% = 100점
    if "이자보상비율" in ratios:
        v = ratios["이자보상비율"]
        scores["이자보상비율"] = min(100, max(0, v * 10))  # 10배 = 100점

    # Overall grade
    if scores:
        avg = sum(scores.values()) / len(scores)
        if avg >= 80:
            grade = "우수"
        elif avg >= 60:
            grade = "양호"
        elif avg >= 40:
            grade = "보통"
        elif avg >= 20:
            grade = "주의"
        else:
            grade = "위험"
    else:
        avg = 0
        grade = "판단불가"

    return {
        "period": latest_period,
        "ratios": ratios,
        "scores": scores,
        "average_score": round(avg, 1),
        "grade": grade,
    }
