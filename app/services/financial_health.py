"""재무건전성 지표 계산 서비스 — 엑셀 템플릿 기준 (8개 지표, 100점)."""

from typing import Optional
from app.database import get_db


# ─── 점수 계산 규칙 ──────────────────────────────────────────────────────────

def _score_current_ratio(v: float) -> int:
    """유동비율(%) 배점 20점."""
    if v >= 150: return 20
    if v >= 100: return 14
    if v >= 80:  return 8
    return 3

def _score_debt_ratio(v: float) -> int:
    """부채비율(%) 배점 15점. 낮을수록 좋음."""
    if v <= 100: return 15
    if v <= 150: return 11
    if v <= 200: return 6
    return 2

def _score_interest_coverage(v: float) -> int:
    """이자보상배율(배) 배점 10점."""
    if v >= 5: return 10
    if v >= 2: return 7
    if v >= 1: return 4
    return 0

def _score_operating_margin(v: float) -> int:
    """영업이익률(%) 배점 20점."""
    if v >= 7: return 20
    if v >= 3: return 14
    if v >= 0: return 8
    return 0

def _score_roe(v: float) -> int:
    """ROE(%) 배점 10점."""
    if v >= 10: return 10
    if v >= 5:  return 7
    if v >= 0:  return 4
    return 0

def _score_revenue_growth(v: float) -> int:
    """매출액증가율(%) 배점 10점."""
    if v >= 10:  return 10
    if v >= 0:   return 7
    if v >= -5:  return 4
    return 0

def _score_ar_days(v: float) -> int:
    """매출채권회전일수(일) 배점 8점. 낮을수록 좋음."""
    if v <= 45:  return 8
    if v <= 90:  return 5
    if v <= 120: return 2
    return 0

def _score_operating_cf(v: float) -> int:
    """영업현금흐름(백만원) 배점 7점."""
    if v > 0:    return 7
    if v > -100: return 4
    return 0

def _item_grade(score: int, max_score: int) -> str:
    """개별 항목 등급 (A/B/C/D)."""
    if max_score == 0:
        return "N/A"
    ratio = score / max_score
    if ratio >= 0.8: return "A (양호)"
    if ratio >= 0.6: return "B (보통)"
    if ratio >= 0.4: return "C (주의)"
    return "D (위험)"

def _total_grade(total: int) -> str:
    if total >= 85: return "AAA"
    if total >= 75: return "AA"
    if total >= 65: return "A"
    if total >= 55: return "BBB"
    if total >= 45: return "BB"
    return "B"

def _recommendation(total: int) -> str:
    if total >= 75: return "✅ 거래 계속 (정상)"
    if total >= 55: return "⚠️ 조건부 거래 (모니터링 강화)"
    return "🚫 거래 재검토 필요"


# ─── DB 조회 헬퍼 ────────────────────────────────────────────────────────────

def _get_ratio(conn, import_id: int, section: str, metric: str, period: str) -> Optional[float]:
    """period 내 첫 번째 행(회사값)을 반환. 없으면 None."""
    row = conn.execute(
        "SELECT value_num FROM report_values "
        "WHERE import_id=? AND section=? AND metric=? AND period=? AND value_num IS NOT NULL "
        "ORDER BY id LIMIT 1",
        (import_id, section, metric, period),
    ).fetchone()
    return row["value_num"] if row else None


def _latest_period(conn, import_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT period FROM report_values "
        "WHERE import_id=? AND period != '-' ORDER BY period DESC LIMIT 1",
        (import_id,),
    ).fetchone()
    return row["period"] if row else None


# ─── 메인 계산 함수 ──────────────────────────────────────────────────────────

def calculate_health(company_id: int) -> dict:
    """8개 지표 100점 만점 재무건전성 평가."""
    with get_db() as conn:
        period = _latest_period(conn, company_id)
        if not period:
            return {"error": "데이터 없음", "domains": [], "total_score": 0, "grade": "-", "period": ""}

        def get(section, metric):
            return _get_ratio(conn, company_id, section, metric, period)

        # 8개 지표값 수집
        current_ratio = get("안정성지표",   "유동비율(%)")
        debt_ratio    = get("안정성지표",   "부채비율(%)")
        interest_cov  = get("수익성지표",   "이자보상배율(배)")
        op_margin     = get("주요재무지표", "매출액영업이익률(%)")
        roe           = get("수익성지표",   "자기자본순이익률(%)")
        rev_growth    = get("주요재무지표", "매출액증가율(%)")
        ar_turnover   = get("활동성지표",   "매출채권회전율(회)")
        op_cf         = get("현금흐름분석", "영업활동 현금흐름")

    # 매출채권회전율 → 회전일수 변환
    ar_days = round(365 / ar_turnover, 1) if ar_turnover and ar_turnover > 0 else None

    def make_item(label, value, unit, benchmark, max_score, score_fn):
        if value is None:
            return {
                "label": label, "value": None, "unit": unit,
                "benchmark": benchmark, "max_score": max_score,
                "score": 0, "item_grade": "N/A",
            }
        score = score_fn(value)
        return {
            "label": label,
            "value": round(value, 2),
            "unit": unit,
            "benchmark": benchmark,
            "max_score": max_score,
            "score": score,
            "item_grade": _item_grade(score, max_score),
        }

    domains = [
        {
            "name": "안전성",
            "max_score": 45,
            "items": [
                make_item("유동비율",     current_ratio, "%",  "100% 이상", 20, _score_current_ratio),
                make_item("부채비율",     debt_ratio,    "%",  "150% 이하", 15, _score_debt_ratio),
                make_item("이자보상배율", interest_cov,  "배", "3배 이상",  10, _score_interest_coverage),
            ],
        },
        {
            "name": "수익성",
            "max_score": 30,
            "items": [
                make_item("영업이익률", op_margin, "%", "5% 이상", 20, _score_operating_margin),
                make_item("ROE",        roe,       "%", "8% 이상", 10, _score_roe),
            ],
        },
        {
            "name": "성장성",
            "max_score": 10,
            "items": [
                make_item("매출액증가율", rev_growth, "%", "5% 이상", 10, _score_revenue_growth),
            ],
        },
        {
            "name": "활동성",
            "max_score": 8,
            "items": [
                make_item("매출채권회전일수", ar_days, "일", "60일 이하", 8, _score_ar_days),
            ],
        },
        {
            "name": "현금흐름",
            "max_score": 7,
            "items": [
                make_item("영업현금흐름", op_cf, "백만원", "양(+)값", 7, _score_operating_cf),
            ],
        },
    ]

    # 도메인별 점수 합산
    for d in domains:
        d["score"] = sum(i["score"] for i in d["items"])

    total = sum(d["score"] for d in domains)

    return {
        "period": period,
        "total_score": total,
        "grade": _total_grade(total),
        "recommendation": _recommendation(total),
        "domains": domains,
    }
