import io
import zipfile
from datetime import date
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from openpyxl.workbook.properties import CalcProperties

from reports.db import get_db
from reports.services.financial_health import calculate_health, get_operating_cashflow

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "assets" / "health_template.xlsx"


def _period_key(period: str) -> tuple[int, int, str]:
    year = -1
    month = -1
    if "." in period:
        year_part, month_part = period.split(".", 1)
        if year_part.isdigit():
            year = int(year_part)
        if month_part.isdigit():
            month = int(month_part)
    return (year, month, period)


def _recent_periods(company_id: int, limit: int = 3) -> list[str]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND period IS NOT NULL AND period != '-'",
            (company_id,),
        ).fetchall()

    periods = sorted({row["period"] for row in rows}, key=_period_key, reverse=True)
    return list(reversed(periods[:limit]))


def _candidate_rank(row) -> tuple[int, int]:
    category = row["category"]
    value_num = row["value_num"]

    if category == "당사":
        category_rank = 0
    elif category is None:
        category_rank = 1
    elif category == "산업평균":
        category_rank = 3
    else:
        category_rank = 2

    value_rank = 0 if value_num is not None else 1
    return (category_rank, value_rank)


def _normalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    if "백만원" in unit:
        return "백만원"
    if "천원" in unit:
        return "천원"
    if "억원" in unit:
        return "억원"
    if "원" in unit:
        return "원"
    if "%" in unit:
        return "%"
    if "배" in unit:
        return "배"
    if "일" in unit:
        return "일"
    if "명" in unit:
        return "명"
    return unit.split(",")[0].strip()


def _convert_value(value: float | None, unit: str | None, target_unit: str) -> float | None:
    if value is None:
        return None

    source_unit = _normalize_unit(unit)
    if not source_unit or source_unit == target_unit:
        return value

    conversions = {
        ("원", "백만원"): value / 1_000_000,
        ("원", "천원"): value / 1_000,
        ("천원", "백만원"): value / 1_000,
        ("백만원", "억원"): value / 100,
        ("천원", "억원"): value / 100_000,
        ("원", "억원"): value / 100_000_000,
    }
    converted = conversions.get((source_unit, target_unit))
    return round(converted, 2) if converted is not None else None


def _select_row(rows: list[dict], period: str, aliases: list[str], *, submetric: str | None = None) -> Optional[dict]:
    candidates = []
    for row in rows:
        if row["period"] != period:
            continue
        if submetric is not None and row["submetric"] != submetric:
            continue
        if row["value_num"] is None:
            continue
        candidates.append(row)

    for alias in aliases:
        exact_matches = [row for row in candidates if row["metric"] == alias]
        if exact_matches:
            return min(exact_matches, key=_candidate_rank)

    for alias in aliases:
        contains_matches = [row for row in candidates if alias in row["metric"]]
        if contains_matches:
            return min(contains_matches, key=_candidate_rank)

    return None


def _value_from_rows(
    rows: list[dict],
    period: str,
    aliases: list[str],
    *,
    target_unit: str | None = None,
    submetric: str | None = None,
) -> float | None:
    row = _select_row(rows, period, aliases, submetric=submetric)
    if not row:
        return None
    value = row["value_num"]
    if target_unit:
        return _convert_value(value, row["unit"], target_unit)
    return value


def _text_or_empty(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _set_number(ws, cell_ref: str, value: float | int | None) -> None:
    ws[cell_ref] = None if value is None else value


def _set_text(ws, cell_ref: str, value: object) -> None:
    ws[cell_ref] = _text_or_empty(value)


def _domain_item(health: dict, domain_name: str, label: str) -> Optional[dict]:
    for domain in health.get("domains", []):
        if domain["name"] != domain_name:
            continue
        for item in domain["items"]:
            if item["label"] == label:
                return item
    return None


def _grade_action(grade: str) -> str:
    actions = {
        "AAA": "적극 거래 권장 / 여신한도 확대 검토",
        "AA": "거래 계속 / 정기 모니터링 유지",
        "A": "거래 계속 / 일부 지표 점검",
        "BBB": "조건부 거래 / 결제조건 재검토",
        "BB": "거래 축소 / 선결제 또는 담보 요구",
        "B": "거래 재검토 / 신규 수주 중단 검토",
    }
    return actions.get(grade, "")


def _monitoring_reason(health: dict) -> str:
    negatives = []
    for domain in health.get("domains", []):
        for item in domain["items"]:
            if item["item_grade"].startswith("D"):
                negatives.append(item["label"])
    if negatives:
        return f"취약 지표: {', '.join(negatives[:3])}"
    return health.get("recommendation", "")


def _collect_export_data(company_id: int) -> dict:
    periods = _recent_periods(company_id)
    if len(periods) < 3:
        periods = (["", "", ""] + periods)[-3:]

    with get_db() as conn:
        company_row = conn.execute(
            "SELECT id, company_name, representatives, biz_no, report_date, industry, main_product "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
        company = dict(company_row) if company_row else {}

        rows = [
            dict(row)
            for row in conn.execute(
                "SELECT section, metric, period, value_num, value_raw, unit, category, submetric, row_no "
                "FROM report_values WHERE import_id = ? ORDER BY row_no, period",
                (company_id,),
            ).fetchall()
        ]

    health = calculate_health(company_id)

    row_map = {
        "재무상태표": {
            11: ["유동자산"],
            12: ["현금및현금성자산", "현금및현금성자산(계)"],
            13: ["매출채권", "매출채권및기타채권", "매출채권 및 기타채권"],
            14: ["재고자산"],
            15: ["비유동자산", "비유동자산(계)"],
            16: ["자산총계"],
            17: ["유동부채"],
            18: ["단기차입금", "단기차입금및유동성장기부채", "유동성장기부채"],
            19: ["매입채무", "매입채무및기타채무", "매입채무 및 기타채무"],
            20: ["비유동부채", "비유동부채(계)"],
            21: ["장기차입금", "장기차입금및사채", "장기차입금"],
            22: ["부채총계"],
            23: ["자본총계"],
        },
        "손익계산서": {
            25: ["매출액"],
            26: ["매출원가"],
            27: ["매출총이익", "매출총이익(손실)"],
            28: ["영업이익", "영업이익(손실)", "영업이익（손실）"],
            30: ["이자비용"],
            31: ["법인세차감전순이익", "법인세비용차감전계속사업이익(손실)", "법인세비용차감전순이익"],
            32: ["당기순이익", "당기순이익(손실)", "당기순이익（손실）"],
        },
        "현금흐름표": {
            35: ["투자활동 현금흐름", "투자활동으로인한현금흐름"],
            36: ["재무활동 현금흐름", "재무활동으로인한현금흐름"],
        },
        "기타정보": {
            38: ["종업원수"],
            39: ["감가상각비", "감각상각비(백만원)", "감가상각비(백만원)"],
            40: ["설비투자", "설비투자(CAPEX)", "유형자산취득"],
        },
    }

    period_values: dict[str, dict[int, float | None]] = {period: {} for period in periods if period}
    for period in periods:
        if not period:
            continue
        for section_name, mappings in row_map.items():
            for row_no, aliases in mappings.items():
                if section_name == "기타정보" and row_no == 38:
                    value = _value_from_rows(rows, period, aliases, target_unit=None)
                else:
                    value = _value_from_rows(rows, period, aliases, target_unit="백만원")
                period_values[period][row_no] = value

        period_values[period][29] = _value_from_rows(rows, period, ["EBITDA"], target_unit="백만원")
        period_values[period][34] = None

    with get_db() as conn:
        for period in periods:
            if not period:
                continue
            period_values[period][34] = get_operating_cashflow(conn, company_id, period)
            if period_values[period][39] is None:
                period_values[period][39] = _value_from_rows(rows, period, ["감가상각비", "감각상각비(백만원)"], target_unit="백만원")

    latest_period = periods[-1] if periods else ""
    current_grade = health.get("grade", "")
    current_score = health.get("total_score", 0)

    return {
        "company": company,
        "health": health,
        "rows": rows,
        "periods": periods,
        "period_values": period_values,
        "latest_period": latest_period,
        "current_grade": current_grade,
        "current_score": current_score,
    }


def _fill_input_sheet(ws, export_data: dict) -> None:
    company = export_data["company"]
    periods = export_data["periods"]
    period_values = export_data["period_values"]

    period_columns = {"C": periods[0] if len(periods) > 0 else "", "D": periods[1] if len(periods) > 1 else "", "E": periods[2] if len(periods) > 2 else ""}

    _set_text(ws, "E5", company.get("company_name", ""))
    _set_text(ws, "E6", company.get("biz_no", ""))
    _set_text(ws, "E7", periods[-1].split(".")[1] if periods and periods[-1] else "")
    _set_text(ws, "E8", company.get("report_date") or str(date.today()))
    _set_text(ws, "E9", company.get("main_product", ""))
    _set_text(ws, "E41", "해당없음")

    for col, period in period_columns.items():
        if not period:
            continue
        for row_no, value in period_values[period].items():
            _set_number(ws, f"{col}{row_no}", value)


def _to_excel_ratio(value: float | None, unit: str) -> float | None:
    """% 단위는 소수로 변환 (80.49% → 0.8049). 배/일/백만원은 그대로."""
    if value is None:
        return None
    if unit == "%":
        return round(value / 100, 6)
    return value


def _value_from_section(
    rows: list[dict],
    period: str,
    section: str,
    aliases: list[str],
) -> Optional[float]:
    """특정 섹션에서만 지표 값을 검색."""
    section_rows = [r for r in rows if r.get("section") == section]
    return _value_from_rows(section_rows, period, aliases)


def _safe_div(a: float | None, b: float | None) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return round(a / b, 6)


def _turnover_days(v: float | None) -> Optional[float]:
    """회전율(회) → 회전일수(일). 단위가 % 라도 값은 회전횟수."""
    return round(365 / v, 2) if v and v > 0 else None


def _ratio_for_period(
    rows: list[dict],
    period: str,
    period_values: dict,
    prev_period_values: Optional[dict],
) -> dict[int, tuple[float | None, str]]:
    """재무비율 분석 시트 행번호 → (값, number_format) 반환.
    % 지표는 소수(÷100), 배 지표는 그대로, 일·백만원은 별도 포맷 지정.
    """
    def pct(v):
        return round(v / 100, 6) if v is not None else None

    def sec(section, aliases):
        return _value_from_section(rows, period, section, aliases)

    pv   = period_values or {}
    ppv  = prev_period_values or {}

    PCT  = "0.0%;\\(0.0%\\);\\-"   # 기존 템플릿 포맷 유지
    NUM2 = "0.00;\\(0.00\\);\\-"   # 배 단위 (소수 2자리)
    DAYS = "#,##0.0;\\(#,##0.0\\);\\-"  # 일·백만원 단위

    return {
        # ── 안전성 ────────────────────────────────────────────
        4:  (pct(sec("안정성지표", ["유동비율(%)"])),         PCT),
        5:  (pct(sec("안정성지표", ["부채비율(%)"])),          PCT),
        6:  (pct(sec("안정성지표", ["자기자본비율(%)"])),       PCT),
        7:  (pct(sec("안정성지표", ["차입금의존도(%)"])),       PCT),
        8:  (sec("수익성지표", ["이자보상배율(배)"]),           NUM2),
        9:  (_safe_div(
                (pv.get(18) or 0) + (pv.get(21) or 0) - (pv.get(12) or 0),
                pv.get(29),
             ), NUM2),
        # ── 수익성 ────────────────────────────────────────────
        11: (pct(sec("수익성지표", ["매출액총이익률(%)"])),     PCT),
        12: (pct(sec("수익성지표", ["매출액영업이익률(%)"])
                 or sec("주요재무지표", ["매출액영업이익률(%)"])), PCT),
        13: (pct(sec("수익성지표", ["매출액순이익률(%)"])),     PCT),
        14: (pct(sec("수익성지표", ["총자본순이익률(%)"])),     PCT),
        15: (pct(sec("수익성지표", ["자기자본순이익률(%)"])),   PCT),
        # ── 성장성 ────────────────────────────────────────────
        17: (pct(sec("성장성지표", ["매출액증가율(%)"])
                 or sec("주요재무지표", ["매출액증가율(%)"])),  PCT),
        18: (_safe_div(
                (pv.get(28) - ppv.get(28)) if (pv.get(28) is not None and ppv.get(28) is not None) else None,
                ppv.get(28),
             ), PCT),
        19: (_safe_div(
                (pv.get(16) - ppv.get(16)) if (pv.get(16) is not None and ppv.get(16) is not None) else None,
                ppv.get(16),
             ), PCT),
        # ── 활동성 ────────────────────────────────────────────
        21: (_turnover_days(sec("활동성지표", ["매출채권회전율(회)"])), DAYS),
        22: (_turnover_days(sec("활동성지표", ["재고자산회전율(회)"])), DAYS),
        23: (_turnover_days(sec("활동성지표", ["매입채무회전율(회)"])), DAYS),
        # ── 현금흐름 ──────────────────────────────────────────
        25: (pv.get(34),                                              DAYS),
        26: (
                (pv.get(34) - pv.get(40))
                if (pv.get(34) is not None and pv.get(40) is not None)
                else pv.get(34),  # CAPEX 미확보 시 영업현금흐름으로 대체
                DAYS,
            ),
    }


def _set_cell(ws, cell_ref: str, value: float | int | str | None, number_format: Optional[str] = None) -> None:
    """값과 셀 포맷을 함께 설정."""
    cell = ws[cell_ref]
    cell.value = value
    if number_format is not None:
        cell.number_format = number_format


def _fill_ratio_sheet(ws, export_data: dict) -> None:
    """재무비율 분석 시트 C/D/E열에 3개 기간 비율 값을 직접 기입."""
    periods = export_data["periods"]
    rows = export_data["rows"]
    period_values = export_data["period_values"]

    col_map = {"C": 0, "D": 1, "E": 2}

    for col, idx in col_map.items():
        period = periods[idx] if idx < len(periods) else ""
        if not period:
            continue
        pv   = period_values.get(period, {})
        prev = period_values.get(periods[idx - 1]) if idx > 0 and periods[idx - 1] else None
        ratios = _ratio_for_period(rows, period, pv, prev)
        for row_no, (value, fmt) in ratios.items():
            _set_cell(ws, f"{col}{row_no}", value, fmt)


def _fill_summary_sheet(ws, export_data: dict) -> None:
    company = export_data["company"]
    health = export_data["health"]

    _set_text(ws, "D3", company.get("company_name", ""))
    _set_text(ws, "D4", company.get("report_date") or str(date.today()))
    _set_text(ws, "D5", company.get("main_product", ""))
    _set_text(ws, "D6", "해당없음")

    # 항목별 평가 행 (종합 평가표 기준)
    summary_rows = [
        (10, "안전성",  "유동비율"),
        (11, "안전성",  "부채비율"),
        (12, "안전성",  "이자보상배율"),
        (13, "수익성",  "영업이익률"),
        (14, "수익성",  "ROE"),
        (15, "성장성",  "매출액증가율"),
        (16, "활동성",  "매출채권회전일수"),
        (17, "현금흐름", "영업현금흐름"),
    ]

    raw_total = 0
    for row_no, domain, label in summary_rows:
        item = _domain_item(health, domain, label)
        if not item:
            continue
        # E열: 당기값 (% → 소수, 나머지 그대로)
        excel_val = _to_excel_ratio(item["value"], item["unit"])
        _set_number(ws, f"E{row_no}", excel_val)
        # F열: 환산점수
        _set_number(ws, f"F{row_no}", item["score"])
        # G열: 등급
        _set_text(ws, f"G{row_no}", item["item_grade"])
        # H열: 종합의견
        if item["value"] is None:
            comment = f"{label}: 데이터 없음"
        else:
            comment = f"{label} {item['value']}{item['unit']} / {item['item_grade']}"
        _set_text(ws, f"H{row_no}", comment)
        raw_total += item["score"]

    # F18: 합계
    _set_number(ws, "F18", raw_total)
    # 종합 등급 판정 (D21-D23)
    _set_number(ws, "D21", health.get("total_score"))
    _set_text(ws, "D22", health.get("grade"))
    _set_text(ws, "D23", health.get("recommendation"))


def _fill_portfolio_sheet(ws, export_data: dict) -> None:
    company = export_data["company"]
    health = export_data["health"]
    rows = export_data["rows"]

    current_ratio = _domain_item(health, "안전성", "유동비율")
    debt_ratio = _domain_item(health, "안전성", "부채비율")
    op_margin = _domain_item(health, "수익성", "영업이익률")
    roe = _domain_item(health, "수익성", "ROE")
    rev_growth = _domain_item(health, "성장성", "매출액증가율")
    interest_cov = _domain_item(health, "안전성", "이자보상배율")
    op_cf = _domain_item(health, "현금흐름", "영업현금흐름")

    latest_period = export_data["latest_period"]
    sales = _value_from_rows(rows, latest_period, ["매출액(백만원)", "매출액"], target_unit="억원")

    _set_text(ws, "B4", company.get("company_name", ""))
    _set_number(ws, "C4", current_ratio["value"] if current_ratio else None)
    _set_number(ws, "D4", debt_ratio["value"] if debt_ratio else None)
    _set_number(ws, "E4", op_margin["value"] if op_margin else None)
    _set_number(ws, "F4", roe["value"] if roe else None)
    _set_number(ws, "G4", sales)
    _set_number(ws, "H4", rev_growth["value"] if rev_growth else None)
    _set_number(ws, "I4", interest_cov["value"] if interest_cov else None)
    _set_number(ws, "J4", op_cf["value"] if op_cf else None)
    _set_number(ws, "K4", health.get("total_score"))
    _set_text(ws, "L4", health.get("grade"))


def _fill_monitoring_sheet(ws, export_data: dict) -> None:
    company = export_data["company"]
    health = export_data["health"]

    _set_number(ws, "A3", 1)
    _set_text(ws, "B3", company.get("company_name", ""))
    _set_text(ws, "C3", company.get("report_date") or str(date.today()))
    _set_text(ws, "D3", "")
    _set_number(ws, "E3", None)
    _set_number(ws, "F3", health.get("total_score"))
    _set_text(ws, "H3", "")
    _set_text(ws, "I3", health.get("grade"))
    _set_text(ws, "J3", _monitoring_reason(health))
    _set_text(ws, "K3", _grade_action(health.get("grade", "")))


def _patch_formula_cache(buffer: io.BytesIO, sheet_index: int, cached_values: dict[str, object]) -> io.BytesIO:
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("", namespace)
    ns = {"main": namespace}
    sheet_path = f"xl/worksheets/sheet{sheet_index}.xml"

    source_bytes = buffer.getvalue()
    output = io.BytesIO()

    with zipfile.ZipFile(io.BytesIO(source_bytes), "r") as src_zip, zipfile.ZipFile(output, "w") as dst_zip:
        for item in src_zip.infolist():
            payload = src_zip.read(item.filename)
            if item.filename == sheet_path:
                root = ET.fromstring(payload)
                cell_map = {
                    cell.get("r"): cell
                    for cell in root.findall(".//main:c", ns)
                    if cell.get("r") in cached_values
                }
                for cell_ref, value in cached_values.items():
                    cell = cell_map.get(cell_ref)
                    if cell is None:
                        continue

                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        cell.attrib.pop("t", None)
                        text_value = str(value)
                    else:
                        cell.set("t", "str")
                        text_value = "" if value is None else str(value)

                    value_node = cell.find("main:v", ns)
                    if value_node is None:
                        value_node = ET.SubElement(cell, f"{{{namespace}}}v")
                    value_node.text = text_value

                payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)

            dst_zip.writestr(item, payload)

    output.seek(0)
    return output


def export_health_excel(company_id: int) -> tuple[io.BytesIO, str]:
    export_data = _collect_export_data(company_id)
    company = export_data["company"]
    health = export_data["health"]

    workbook = load_workbook(TEMPLATE_PATH)
    workbook.calculation = CalcProperties(calcMode="auto", fullCalcOnLoad=True, forceFullCalc=True)

    _fill_input_sheet(workbook["재무데이터 입력"], export_data)
    _fill_portfolio_sheet(workbook["고객사 비교 현황"], export_data)
    _fill_monitoring_sheet(workbook["모니터링 이력"], export_data)

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    buffer = _patch_formula_cache(
        buffer,
        sheet_index=3,
        cached_values={
            "D3": company.get("company_name", ""),
            "D4": company.get("report_date") or str(date.today()),
            "D5": company.get("main_product", ""),
            "D6": "해당없음",
            "D21": health.get("total_score", 0),
            "D22": health.get("grade", ""),
            "D23": health.get("recommendation", ""),
        },
    )
    return buffer, company.get("company_name", str(company_id))
