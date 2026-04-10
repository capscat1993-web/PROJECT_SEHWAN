"""재무건전성 지표 계산 서비스 - 엑셀 템플릿 기준 (8개 지표, 100점)."""

from typing import Optional

from reports.db import get_db


def _score_current_ratio(v: float) -> int:
    """유동비율(%) 배점 20점."""
    if v >= 150:
        return 20
    if v >= 100:
        return 14
    if v >= 80:
        return 8
    return 3


def _score_debt_ratio(v: float) -> int:
    """부채비율(%) 배점 15점. 낮을수록 좋음."""
    if v <= 100:
        return 15
    if v <= 150:
        return 11
    if v <= 200:
        return 6
    return 2


def _score_interest_coverage(v: float) -> int:
    """이자보상배율(배) 배점 10점."""
    if v >= 5:
        return 10
    if v >= 2:
        return 7
    if v >= 1:
        return 4
    return 0


def _score_operating_margin(v: float) -> int:
    """영업이익률(%) 배점 20점."""
    if v >= 7:
        return 20
    if v >= 3:
        return 14
    if v >= 0:
        return 8
    return 0


def _score_roe(v: float) -> int:
    """ROE(%) 배점 10점."""
    if v >= 10:
        return 10
    if v >= 5:
        return 7
    if v >= 0:
        return 4
    return 0


def _score_revenue_growth(v: float) -> int:
    """매출액증가율(%) 배점 10점."""
    if v >= 10:
        return 10
    if v >= 0:
        return 7
    if v >= -5:
        return 4
    return 0


def _score_ar_days(v: float) -> int:
    """매출채권회전일수(일) 배점 8점. 낮을수록 좋음."""
    if v <= 45:
        return 8
    if v <= 90:
        return 5
    if v <= 120:
        return 2
    return 0


def _score_operating_cf(v: float) -> int:
    """영업현금흐름(백만원) 배점 7점."""
    if v > 0:
        return 7
    if v > -100:
        return 4
    return 0


def _item_grade(score: int, max_score: int) -> str:
    """개별 항목 등급 (A/B/C/D)."""
    if max_score == 0:
        return "N/A"
    ratio = score / max_score
    if ratio >= 0.8:
        return "A (양호)"
    if ratio >= 0.6:
        return "B (보통)"
    if ratio >= 0.4:
        return "C (주의)"
    return "D (위험)"


def _total_grade(total: int) -> str:
    if total >= 85:
        return "AAA"
    if total >= 75:
        return "AA"
    if total >= 65:
        return "A"
    if total >= 55:
        return "BBB"
    if total >= 45:
        return "BB"
    return "B"


def _recommendation(total: int) -> str:
    if total >= 75:
        return "거래 계속 (정상)"
    if total >= 55:
        return "조건부 거래 (모니터링 강화)"
    return "재검토 필요"


_GRADE_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B"]


def _cap_grade(grade: str, highest_allowed: str) -> str:
    try:
        grade_idx = _GRADE_ORDER.index(grade)
        allowed_idx = _GRADE_ORDER.index(highest_allowed)
    except ValueError:
        return grade
    return _GRADE_ORDER[max(grade_idx, allowed_idx)]


def _get_ratio(conn, import_id: int, section: str, metric: str, period: str) -> Optional[float]:
    """period 기준 첫 번째 회사값만 반환. 없으면 None."""
    row = conn.execute(
        "SELECT value_num FROM report_values "
        "WHERE import_id=? AND section=? AND metric=? AND period=? AND value_num IS NOT NULL "
        "ORDER BY CASE "
        "WHEN category='당사' THEN 0 "
        "WHEN category IS NULL THEN 1 "
        "WHEN category='산업평균' THEN 3 "
        "ELSE 2 END, id LIMIT 1",
        (import_id, section, metric, period),
    ).fetchone()
    return row["value_num"] if row else None


def _get_ratio_with_submetric(
    conn,
    import_id: int,
    section: str,
    metric: str,
    period: str,
    submetric: str,
) -> Optional[float]:
    row = conn.execute(
        "SELECT value_num FROM report_values "
        "WHERE import_id=? AND section=? AND metric=? AND period=? AND submetric=? "
        "AND value_num IS NOT NULL "
        "ORDER BY CASE "
        "WHEN category='당사' THEN 0 "
        "WHEN category IS NULL THEN 1 "
        "WHEN category='산업평균' THEN 3 "
        "ELSE 2 END, id LIMIT 1",
        (import_id, section, metric, period, submetric),
    ).fetchone()
    return row["value_num"] if row else None


def get_operating_cashflow(conn, import_id: int, period: str) -> Optional[float]:
    """영업활동 현금흐름 원시값 우선, 없으면 현금흐름 비율로 추정."""
    raw_metric_candidates = [
        ("현금흐름분석", "영업활동 현금흐름"),
        ("현금흐름표", "영업활동으로인한현금흐름"),
        ("현금흐름표", "영업활동으로인한현금흐름"),
    ]
    for section, metric in raw_metric_candidates:
        value = _get_ratio(conn, import_id, section, metric, period)
        if value is not None:
            return value

    cf_ratio = _get_ratio(conn, import_id, "현금흐름지표", "손익활동CF/매출액(%)", period)
    if cf_ratio is None:
        cf_ratio = _get_ratio(conn, import_id, "주요재무지표", "영업활동CF/차입금(%)", period)

    sales_amount = _get_ratio(conn, import_id, "규모지표", "매출액(백만원)", period)
    if sales_amount is None:
        sales_amount = _get_ratio_with_submetric(conn, import_id, "수익성진단", "매출액", period, "금액")

    if cf_ratio is not None and sales_amount is not None:
        return round(sales_amount * (cf_ratio / 100), 2)

    return None


def _latest_period(conn, import_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT period FROM report_values "
        "WHERE import_id=? AND period != '-' ORDER BY period DESC LIMIT 1",
        (import_id,),
    ).fetchone()
    return row["period"] if row else None


def _find_item(domains: list[dict], label: str) -> Optional[dict]:
    for domain in domains:
        for item in domain["items"]:
            if item["label"] == label:
                return item
    return None


def _fmt_metric(item: Optional[dict]) -> str:
    if not item or item["value"] is None:
        return "-"
    value = item["value"]
    unit = item["unit"]
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "배":
        return f"{value:.2f}배"
    if unit == "일":
        return f"{value:.1f}일"
    if unit == "백만원":
        return f"{value:,.0f}백만원"
    return f"{value}"


def _score_ratio(item: Optional[dict]) -> float:
    if not item or item["max_score"] == 0:
        return -1
    return item["score"] / item["max_score"]


def _build_evaluation_opinion(
    grade: str,
    total_score: int,
    recommendation: str,
    domains: list[dict],
    data_note: str,
) -> list[str]:
    cr = _find_item(domains, "유동비율")
    dr = _find_item(domains, "부채비율")
    ic = _find_item(domains, "이자보상배율")
    om = _find_item(domains, "영업이익률")
    roe = _find_item(domains, "ROE")
    rg = _find_item(domains, "매출액증가율")
    ar = _find_item(domains, "매출채권회전일수")
    cf = _find_item(domains, "영업현금흐름")

    def v(item):
        return item["value"] if item and item["value"] is not None else None

    cr_v, dr_v, ic_v = v(cr), v(dr), v(ic)
    om_v, roe_v, rg_v = v(om), v(roe), v(rg)
    ar_v, cf_v = v(ar), v(cf)

    # ── Line 1: 종합 판정 + 안전성 ─────────────────────────────
    # 등급별 전반적 판단
    if grade in ("AAA", "AA"):
        overall = "재무구조가 매우 안정적이며 신용위험이 낮은 수준으로 평가됩니다"
    elif grade == "A":
        overall = "전반적인 재무건전성은 양호하나 일부 지표에 대한 지속적인 모니터링이 필요합니다"
    elif grade == "BBB":
        overall = "재무건전성은 평균 수준이나 취약 지표에 대한 선제적 관리가 요구됩니다"
    elif grade == "BB":
        overall = "일부 재무지표에서 리스크 신호가 감지되며 거래조건 재검토를 권고합니다"
    else:
        overall = "복수의 재무지표에서 경보 수준의 부담이 확인되어 신중한 접근이 필요합니다"

    # 안전성 세부 진단
    stability_parts = []
    if cr_v is not None:
        if cr_v >= 150:
            stability_parts.append(f"유동비율 {cr_v:.0f}%로 단기 지급여력이 충분합니다")
        elif cr_v >= 100:
            stability_parts.append(f"유동비율 {cr_v:.0f}%로 단기 유동성은 기준선을 유지하고 있습니다")
        else:
            stability_parts.append(f"유동비율 {cr_v:.0f}%로 단기 유동성 관리에 주의가 필요합니다")
    if dr_v is not None:
        if dr_v <= 100:
            stability_parts.append(f"부채비율 {dr_v:.0f}%로 자본 대비 차입부담이 낮은 편입니다")
        elif dr_v <= 200:
            stability_parts.append(f"부채비율 {dr_v:.0f}%로 적정 수준이나 추가 레버리지 확대는 자제할 필요가 있습니다")
        else:
            stability_parts.append(f"부채비율 {dr_v:.0f}%로 과도한 차입 의존도가 재무위험을 높이고 있습니다")
    if ic_v is not None:
        if ic_v >= 5:
            stability_parts.append(f"이자보상배율 {ic_v:.1f}배로 이자비용 감당능력이 우수합니다")
        elif ic_v >= 2:
            stability_parts.append(f"이자보상배율 {ic_v:.1f}배로 이자 상환 능력은 보통 수준입니다")
        elif ic_v >= 1:
            stability_parts.append(f"이자보상배율 {ic_v:.1f}배로 이자 감당 여력이 빠듯한 상태입니다")
        else:
            stability_parts.append(f"이자보상배율 {ic_v:.1f}배로 영업이익만으로 이자를 충당하지 못하고 있어 재무 부담이 심각합니다")

    line1 = f"종합 {total_score}점({grade} 등급): {overall}."
    if stability_parts:
        line1 += " " + ", ".join(stability_parts) + "."

    # ── Line 2: 수익성 + 성장성 ────────────────────────────────
    profit_parts = []
    if om_v is not None:
        if om_v >= 7:
            profit_parts.append(f"영업이익률 {om_v:.1f}%로 본업 수익창출력이 견조합니다")
        elif om_v >= 3:
            profit_parts.append(f"영업이익률 {om_v:.1f}%로 수익성은 보통 수준을 유지하고 있습니다")
        elif om_v >= 0:
            profit_parts.append(f"영업이익률 {om_v:.1f}%로 수익성이 낮아 원가·비용 구조 개선이 필요합니다")
        else:
            profit_parts.append(f"영업이익률 {om_v:.1f}%로 영업손실이 발생하고 있어 사업 구조에 대한 재검토가 요구됩니다")
    if roe_v is not None:
        if roe_v >= 10:
            profit_parts.append(f"ROE {roe_v:.1f}%로 자기자본 대비 이익 효율이 높습니다")
        elif roe_v >= 5:
            profit_parts.append(f"ROE {roe_v:.1f}%로 자본 효율성은 보통입니다")
        elif roe_v >= 0:
            profit_parts.append(f"ROE {roe_v:.1f}%로 자본 수익성이 미흡합니다")
        else:
            profit_parts.append(f"ROE {roe_v:.1f}%로 자본잠식 가능성을 포함한 손실 구조를 점검해야 합니다")
    if rg_v is not None:
        if rg_v >= 10:
            profit_parts.append(f"매출 성장률 {rg_v:.1f}%로 외형 확장이 뚜렷합니다")
        elif rg_v >= 0:
            profit_parts.append(f"매출 성장률 {rg_v:.1f}%로 완만한 성장세를 이어가고 있습니다")
        elif rg_v >= -5:
            profit_parts.append(f"매출이 {abs(rg_v):.1f}% 감소해 성장 동력이 약화되고 있습니다")
        else:
            profit_parts.append(f"매출이 {abs(rg_v):.1f}% 급감해 사업 환경 악화 여부를 면밀히 살펴야 합니다")

    if profit_parts:
        line2 = " ".join(f"{p}." for p in profit_parts)
    else:
        line2 = "수익성·성장성 지표 데이터가 충분하지 않아 해당 영역의 평가는 제한적입니다."

    # ── Line 3: 현금흐름 + 매출채권 + 종합 리스크 신호 ──────────
    cf_parts = []
    if cf_v is not None:
        if cf_v > 0:
            cf_parts.append(
                f"영업현금흐름 {cf_v:,.0f}백만원(양(+))으로 회계이익이 실제 현금창출로 연결되고 있어 자금 건전성 측면에서 긍정적입니다"
            )
        else:
            cf_parts.append(
                f"영업현금흐름이 {cf_v:,.0f}백만원(음(-))으로, 이익 계상에도 불구하고 실제 현금 유출이 발생하고 있어 운전자본 및 결제능력 점검이 필요합니다"
            )
    else:
        cf_parts.append("현금흐름 자료가 확인되지 않아 실제 현금창출력과 차입금 상환 여력은 별도 서류로 확인해야 합니다")

    if ar_v is not None:
        if ar_v <= 45:
            cf_parts.append(f"매출채권회전일수 {ar_v:.0f}일로 대금회수 속도가 빠르고 운전자본 관리가 효율적입니다")
        elif ar_v <= 90:
            cf_parts.append(f"매출채권회전일수 {ar_v:.0f}일로 결제 사이클은 일반적 수준이나 장기 미회수 채권 여부를 확인하십시오")
        else:
            cf_parts.append(
                f"매출채권회전일수 {ar_v:.0f}일로 기준치(60일)를 크게 상회합니다. "
                "대금회수 지연은 유동성 압박과 부실채권 리스크를 동시에 높일 수 있으므로 회수 관리 강화가 요구됩니다"
            )

    line3 = " ".join(f"{p}." for p in cf_parts)

    return [line1, line2, line3]


def calculate_health(company_id: int) -> dict:
    """8개 지표 100점 만점 재무건전성 평가."""
    with get_db() as conn:
        period = _latest_period(conn, company_id)
        if not period:
            return {"error": "데이터 없음", "domains": [], "total_score": 0, "grade": "-", "period": ""}

        def get(section: str, metric: str) -> Optional[float]:
            return _get_ratio(conn, company_id, section, metric, period)

        current_ratio = get("안정성지표", "유동비율(%)")
        debt_ratio = get("안정성지표", "부채비율(%)")
        interest_cov = get("수익성지표", "이자보상배율(배)")
        op_margin = get("주요재무지표", "매출액영업이익률(%)")
        roe = get("수익성지표", "자기자본순이익률(%)")
        rev_growth = get("주요재무지표", "매출액증가율(%)")
        ar_turnover = get("활동성지표", "매출채권회전율(회)")
        op_cf = get_operating_cashflow(conn, company_id, period)

    ar_days = round(365 / ar_turnover, 1) if ar_turnover and ar_turnover > 0 else None

    def make_item(label, value, unit, benchmark, configured_max_score, score_fn):
        if value is None:
            return {
                "label": label,
                "value": None,
                "unit": unit,
                "benchmark": benchmark,
                "max_score": 0,
                "configured_max_score": configured_max_score,
                "score": 0,
                "item_grade": "N/A",
                "is_missing": True,
            }

        score = score_fn(value)
        return {
            "label": label,
            "value": round(value, 2),
            "unit": unit,
            "benchmark": benchmark,
            "max_score": configured_max_score,
            "configured_max_score": configured_max_score,
            "score": score,
            "item_grade": _item_grade(score, configured_max_score),
            "is_missing": False,
        }

    domains = [
        {
            "name": "안전성",
            "items": [
                make_item("유동비율", current_ratio, "%", "100% 이상", 20, _score_current_ratio),
                make_item("부채비율", debt_ratio, "%", "150% 이하", 15, _score_debt_ratio),
                make_item("이자보상배율", interest_cov, "배", "3배 이상", 10, _score_interest_coverage),
            ],
        },
        {
            "name": "수익성",
            "items": [
                make_item("영업이익률", op_margin, "%", "5% 이상", 20, _score_operating_margin),
                make_item("ROE", roe, "%", "8% 이상", 10, _score_roe),
            ],
        },
        {
            "name": "성장성",
            "items": [
                make_item("매출액증가율", rev_growth, "%", "5% 이상", 10, _score_revenue_growth),
            ],
        },
        {
            "name": "활동성",
            "items": [
                make_item("매출채권회전일수", ar_days, "일", "60일 이하", 8, _score_ar_days),
            ],
        },
        {
            "name": "현금흐름",
            "items": [
                make_item("영업현금흐름", op_cf, "백만원", "양(+)값", 7, _score_operating_cf),
            ],
        },
    ]

    for domain in domains:
        domain["configured_max_score"] = sum(item["configured_max_score"] for item in domain["items"])
        domain["max_score"] = sum(item["max_score"] for item in domain["items"])
        domain["score"] = sum(item["score"] for item in domain["items"])

    raw_total = sum(domain["score"] for domain in domains)
    total_possible = sum(domain["max_score"] for domain in domains)
    configured_total = sum(domain["configured_max_score"] for domain in domains)
    total = round(raw_total / total_possible * 100) if total_possible > 0 else 0
    completeness = round(total_possible / configured_total * 100) if configured_total > 0 else 0

    cashflow_missing = op_cf is None
    uncapped_grade = _total_grade(total)
    grade = _cap_grade(uncapped_grade, "A") if cashflow_missing else uncapped_grade
    grade_note = ""
    if grade != uncapped_grade:
        grade_note = "현금흐름 데이터 미확보로 최고등급은 A까지 제한됩니다."
    data_note = ""
    if cashflow_missing:
        data_note = "현금흐름 영역은 평가에서 제외한 뒤 잔여 항목 기준으로 총점을 환산했습니다."

    recommendation = _recommendation(total)
    evaluation_opinion_lines = _build_evaluation_opinion(
        grade=grade,
        total_score=total,
        recommendation=recommendation,
        domains=domains,
        data_note=data_note,
    )

    return {
        "period": period,
        "total_score": total,
        "raw_score": raw_total,
        "total_possible_score": total_possible,
        "configured_total_score": configured_total,
        "data_completeness_pct": completeness,
        "grade": grade,
        "uncapped_grade": uncapped_grade,
        "grade_note": grade_note,
        "data_note": data_note,
        "recommendation": recommendation,
        "evaluation_opinion_lines": evaluation_opinion_lines,
        "domains": domains,
    }
