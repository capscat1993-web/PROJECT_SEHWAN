import json
import os
import urllib.parse

from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .db import get_db
from .services.financial_health import calculate_health
from .services.health_export import export_health_excel

KEY_METRICS = {
    "매출액": ["매출액"],
    "영업이익": ["영업이익（손실）", "영업이익(손실)", "영업이익"],
    "당기순이익": ["당기순이익(손실)", "당기순이익（손실）", "당기순이익"],
}

INCOME_SECTIONS = ["손익계산서", "포괄손익계산서"]


def _dicts(rows):
    return [dict(row) for row in rows]


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


def _normalize_metric_unit(unit: str | None) -> str:
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
    return unit.split(",")[0].strip()


def _convert_metric_value(value: float | None, unit: str | None, target_unit: str) -> float | None:
    if value is None:
        return None

    source_unit = _normalize_metric_unit(unit)
    if not source_unit or not target_unit or source_unit == target_unit:
        return value

    conversions = {
        ("원", "천원"): value / 1_000,
        ("원", "백만원"): value / 1_000_000,
        ("천원", "백만원"): value / 1_000,
        ("백만원", "천원"): value * 1_000,
    }
    converted = conversions.get((source_unit, target_unit))
    return round(converted, 2) if converted is not None else value


def _normalize_period(period: str | None) -> str | None:
    if not period or period == "-":
        return None
    normalized = period.strip().replace("-", ".").replace("/", ".")
    if "." not in normalized:
        return normalized
    year_part, month_part = normalized.split(".", 1)
    if year_part.isdigit() and month_part.isdigit():
        return f"{int(year_part):04d}.{int(month_part):02d}"
    return normalized


def _period_key(period: str | None) -> tuple[int, int, str]:
    normalized = _normalize_period(period)
    if not normalized:
        return (-1, -1, "")
    year = -1
    month = -1
    if "." in normalized:
        year_part, month_part = normalized.split(".", 1)
        if year_part.isdigit():
            year = int(year_part)
        if month_part.isdigit():
            month = int(month_part)
    return (year, month, normalized)


def _recent_periods(company_id: int, limit: int = 3, sections: list[str] | None = None) -> list[str]:
    with get_db() as conn:
        if sections:
            placeholders = ",".join("?" for _ in sections)
            rows = conn.execute(
                f"SELECT DISTINCT period FROM report_values "
                f"WHERE import_id = ? AND section IN ({placeholders}) "
                f"AND period IS NOT NULL AND period != '-'",
                (company_id, *sections),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT period FROM report_values "
                "WHERE import_id = ? AND period IS NOT NULL AND period != '-'",
                (company_id,),
            ).fetchall()

    periods = sorted(
        {_normalize_period(row["period"]) for row in rows if _normalize_period(row["period"])},
        key=_period_key,
        reverse=True,
    )
    return list(reversed(periods[:limit]))


def _recent_financial_periods(company_id: int, limit: int = 3) -> list[str]:
    periods = _recent_periods(
        company_id,
        limit=limit,
        sections=[
            "수익성진단",
            "안정성진단",
            "현금흐름분석",
            "현금흐름지표",
            "주요재무지표",
            "규모지표",
            "성장성지표",
            "수익성지표",
            "안정성지표",
            "활동성지표",
        ],
    )
    return periods or _recent_periods(company_id, limit=limit)


def _financial_table_payload(company_id: int, section: str) -> dict:
    allowed_period_list = _recent_financial_periods(company_id)
    allowed_periods = set(allowed_period_list)
    with get_db() as conn:
        periods = conn.execute(
            "SELECT DISTINCT period FROM report_values "
            "WHERE import_id = ? AND section = ? AND period != '-' ORDER BY period",
            (company_id, section),
        ).fetchall()
        period_list = []
        for row in periods:
            normalized_period = _normalize_period(row["period"])
            if normalized_period in allowed_periods and normalized_period not in period_list:
                period_list.append(normalized_period)
        period_list = sorted(period_list, key=_period_key)

        rows = conn.execute(
            "SELECT metric, period, value_raw, value_num, category, submetric, row_no "
            "FROM report_values "
            "WHERE import_id = ? AND section = ? "
            "ORDER BY row_no",
            (company_id, section),
        ).fetchall()

        unit_row = conn.execute(
            "SELECT unit FROM report_values WHERE import_id = ? AND section = ? AND unit IS NOT NULL LIMIT 1",
            (company_id, section),
        ).fetchone()

    chosen_rows = {}
    row_order = {}
    for row in rows:
        period = _normalize_period(row["period"])
        metric = row["metric"]
        if not period or period == "-" or period not in allowed_periods:
            continue
        key = (metric, period)
        existing = chosen_rows.get(key)
        if existing is None or _candidate_rank(row) < _candidate_rank(existing):
            chosen_rows[key] = row
            row_order.setdefault(metric, row["row_no"])

    ordered_metrics = []
    pivot = {}
    for row in sorted(chosen_rows.values(), key=lambda item: (row_order.get(item["metric"], item["row_no"]), item["period"])):
        category = row["category"]
        show_category = category if category and category not in {"당사"} else None
        metric = f"{row['metric']} ({show_category})" if show_category else row["metric"]
        if metric not in pivot:
            pivot[metric] = {}
            ordered_metrics.append(metric)
        pivot[metric][_normalize_period(row["period"])] = {"raw": row["value_raw"], "num": row["value_num"]}

    table_rows = []
    for metric in ordered_metrics:
        values = {period: pivot[metric].get(period, {"raw": "", "num": None}) for period in period_list}
        table_rows.append({"metric": metric, "values": values})

    return {
        "section": section,
        "periods": period_list or allowed_period_list,
        "rows": table_rows,
        "unit": unit_row["unit"] if unit_row else "",
    }


def _filtered_table_payload(
    company_id: int,
    section: str,
    *,
    submetric: str | None = None,
    metric_order: list[str] | None = None,
    label: str | None = None,
    target_unit: str | None = None,
) -> dict:
    allowed_periods = _recent_financial_periods(company_id)
    allowed_period_set = set(allowed_periods)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT metric, period, value_raw, value_num, unit, submetric, category, row_no "
            "FROM report_values WHERE import_id = ? AND section = ? AND period != '-' "
            "ORDER BY row_no, period",
            (company_id, section),
        ).fetchall()

    filtered_rows = []
    for row in rows:
        if _normalize_period(row["period"]) not in allowed_period_set:
            continue
        if submetric and row["submetric"] != submetric:
            continue
        filtered_rows.append(row)

    pivot = {}
    unit = ""
    for row in filtered_rows:
        metric = row["metric"]
        if metric_order and metric not in metric_order:
            continue
        row_unit = _normalize_metric_unit(row["unit"])
        value_num = row["value_num"]
        value_raw = row["value_raw"]
        if target_unit and row_unit in {"원", "천원", "백만원", "억원"}:
            value_num = _convert_metric_value(value_num, row_unit, target_unit)
            if value_num is None:
                value_raw = ""
            elif float(value_num).is_integer():
                value_raw = f"{int(value_num):,}"
            else:
                value_raw = f"{value_num:,.2f}"
        pivot.setdefault(metric, {})
        pivot[metric][_normalize_period(row["period"])] = {"raw": value_raw, "num": value_num}
        if not unit:
            unit = target_unit or row_unit

    if metric_order:
        ordered_metrics = [metric for metric in metric_order if metric in pivot]
    else:
        ordered_metrics = list(pivot.keys())

    return {
        "section": label or section,
        "periods": allowed_periods,
        "rows": [
            {
                "metric": metric,
                "values": {
                    period: pivot[metric].get(period, {"raw": "", "num": None}) for period in allowed_periods
                },
            }
            for metric in ordered_metrics
        ],
        "unit": unit,
    }


def _financial_statements_payload(company_id: int) -> dict:
    statements = {
        "income": _filtered_table_payload(
            company_id,
            "수익성진단",
            submetric="금액",
            metric_order=[
                "매출액",
                "매출원가",
                "매출총이익",
                "판매비와관리비",
                "영업이익",
                "이자비용",
                "법인세차감전순손익",
                "계속사업이익(손실)",
                "당기순이익",
            ],
            label="손익계산서",
        ),
        "balance": _filtered_table_payload(
            company_id,
            "안정성진단",
            submetric="금액",
            metric_order=[
                "유동자산",
                "당좌자산",
                "재고자산",
                "비유동자산",
                "자산총계",
                "유동부채",
                "비유동부채",
                "부채총계",
                "자본총계",
                "부채와자본총계",
            ],
            label="재무상태표",
        ),
        "cashflow": _filtered_table_payload(
            company_id,
            "현금흐름분석",
            metric_order=[
                "손익활동CF/총부채(%)",
                "손익활동CF/총자본(%)",
                "손익활동CF/매출액(%)",
                "영업활동CF/차입금(%)",
            ],
            label="현금흐름분석",
        ),
    }

    return statements


def _key_metrics_payload(company_id: int) -> dict:
    allowed_periods = _recent_financial_periods(company_id)
    allowed_period_set = set(allowed_periods)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT metric, period, value_num, value_raw, unit, category, row_no "
            "FROM report_values "
            "WHERE import_id = ? "
            "AND section IN ('손익계산서', '포괄손익계산서') "
            "AND period != '-' ORDER BY row_no, period",
            (company_id,),
        ).fetchall()

        diagnostic_rows = conn.execute(
            "SELECT metric, period, value_num, value_raw, unit, submetric, category, row_no "
            "FROM report_values "
            "WHERE import_id = ? AND section = '수익성진단' AND submetric = '금액' AND period != '-' "
            "ORDER BY row_no, period",
            (company_id,),
        ).fetchall()

    periods = allowed_periods
    fallback_metric_names = {
        "매출액": ["매출액"],
        "영업이익": ["영업이익"],
        "당기순이익": ["당기순이익"],
    }
    selected_series = {}
    selected_units = set()
    for label, keywords in KEY_METRICS.items():
        series = {}
        for row in rows:
            normalized_period = _normalize_period(row["period"])
            if normalized_period in allowed_period_set and any(keyword in row["metric"] for keyword in keywords):
                existing = series.get(normalized_period)
                if existing is None:
                    series[normalized_period] = row
                elif _candidate_rank(row) < _candidate_rank(existing):
                    series[normalized_period] = row

        if not series:
            for row in diagnostic_rows:
                normalized_period = _normalize_period(row["period"])
                if normalized_period in allowed_period_set and row["metric"] in fallback_metric_names[label]:
                    series[normalized_period] = row

        for row in series.values():
            normalized_unit = _normalize_metric_unit(row["unit"])
            if normalized_unit:
                selected_units.add(normalized_unit)
        selected_series[label] = series

    normalized_money_units = selected_units & {"원", "천원", "백만원"}
    if normalized_money_units:
        unit = "백만원"
    elif selected_units:
        unit = sorted(selected_units)[0]
    else:
        unit = "백만원"

    metrics = {}
    for label, series in selected_series.items():
        metrics[label] = {
            period: (
                _convert_metric_value(series[period]["value_num"], series[period]["unit"], unit)
                if period in series
                else None
            )
            for period in periods
        }

    return {"periods": periods, "metrics": metrics, "unit": unit}


def _fetch_company_or_404(company_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, company_name, representatives, biz_no, report_date, "
            "industry, main_product, imported_at "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
    if not row:
        raise Http404("Company not found")
    return dict(row)


@require_GET
def root(_request):
    return JsonResponse(
        {
            "service": "financial-report-platform",
            "status": "ok",
            "stack": {
                "backend": "Django",
                "frontend": "Next.js",
                "database": "SQLite",
            },
        }
    )


@require_GET
def healthcheck(_request):
    return JsonResponse({"status": "ok"})


@require_GET
def api_meta(_request):
    return JsonResponse(
        {
            "service": "financial-report-api",
            "status": "ok",
            "docs_hint": "Use /api/overview and /api/companies endpoints from the Next.js frontend.",
        }
    )


@require_GET
def overview(_request):
    with get_db() as conn:
        totals = conn.execute(
            "SELECT COUNT(*) AS total_companies, MAX(report_date) AS latest_report_date FROM report_imports"
        ).fetchone()
        top_industries = conn.execute(
            "SELECT COALESCE(industry, '미분류') AS name, COUNT(*) AS count "
            "FROM report_imports GROUP BY COALESCE(industry, '미분류') "
            "ORDER BY count DESC, name ASC LIMIT 6"
        ).fetchall()
        latest_companies = conn.execute(
            "SELECT id, company_name, industry, main_product, report_date "
            "FROM report_imports ORDER BY imported_at DESC LIMIT 5"
        ).fetchall()
        value_totals = conn.execute("SELECT COUNT(*) AS total_rows FROM report_values").fetchone()

    return JsonResponse(
        {
            "total_companies": totals["total_companies"],
            "latest_report_date": totals["latest_report_date"],
            "total_value_rows": value_totals["total_rows"],
            "top_industries": _dicts(top_industries),
            "latest_companies": _dicts(latest_companies),
        }
    )


@require_GET
def list_companies(request):
    q = request.GET.get("q", "").strip()
    with get_db() as conn:
        params = ()
        where = ""
        if q:
            where = "WHERE company_name LIKE ? OR industry LIKE ? OR main_product LIKE ?"
            like = f"%{q}%"
            params = (like, like, like)
        rows = conn.execute(
            "SELECT id, company_name, representatives, biz_no, report_date, "
            "industry, main_product, imported_at "
            f"FROM report_imports {where} ORDER BY company_name",
            params,
        ).fetchall()
    return JsonResponse(_dicts(rows), safe=False)


@require_GET
def company_detail(_request, company_id: int):
    return JsonResponse(_fetch_company_or_404(company_id))


@require_GET
def company_notes(_request, company_id: int):
    _fetch_company_or_404(company_id)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT row_no, section, line FROM report_notes WHERE import_id = ? ORDER BY row_no LIMIT 120",
            (company_id,),
        ).fetchall()
    return JsonResponse(_dicts(rows), safe=False)


@require_GET
def company_sections(_request, company_id: int):
    _fetch_company_or_404(company_id)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT section FROM report_values WHERE import_id = ? ORDER BY section",
            (company_id,),
        ).fetchall()
    return JsonResponse([row["section"] for row in rows], safe=False)


@require_GET
def company_periods(_request, company_id: int):
    _fetch_company_or_404(company_id)
    return JsonResponse(_recent_periods(company_id), safe=False)


@require_GET
def company_financial(request, company_id: int):
    _fetch_company_or_404(company_id)
    section = request.GET.get("section", "").strip()
    with get_db() as conn:
        if section:
            rows = conn.execute(
                "SELECT metric, period, value_raw, value_num, unit, submetric, category "
                "FROM report_values WHERE import_id = ? AND section = ? ORDER BY row_no",
                (company_id, section),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT section, metric, period, value_raw, value_num, unit, submetric, category "
                "FROM report_values WHERE import_id = ? ORDER BY section, row_no",
                (company_id,),
            ).fetchall()
    return JsonResponse(_dicts(rows), safe=False)


@require_GET
def company_financial_table(request, company_id: int):
    _fetch_company_or_404(company_id)
    section = request.GET.get("section", "재무상태표")
    return JsonResponse(_financial_table_payload(company_id, section))


@require_GET
def company_key_metrics(_request, company_id: int):
    _fetch_company_or_404(company_id)
    return JsonResponse(_key_metrics_payload(company_id))


@require_GET
def company_health(_request, company_id: int):
    _fetch_company_or_404(company_id)
    return JsonResponse(calculate_health(company_id))


@require_GET
def export_health(_request, company_id: int):
    _fetch_company_or_404(company_id)
    buffer, company_name = export_health_excel(company_id)
    filename = urllib.parse.quote(f"{company_name}_재무건전성평가.xlsx")
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
    return response


@require_GET
def company_dashboard(_request, company_id: int):
    company = _fetch_company_or_404(company_id)
    health = calculate_health(company_id)

    with get_db() as conn:
        sections = [row["section"] for row in conn.execute(
            "SELECT DISTINCT section FROM report_values WHERE import_id = ? ORDER BY section",
            (company_id,),
        ).fetchall()]
        notes = conn.execute(
            "SELECT section, line FROM report_notes WHERE import_id = ? ORDER BY row_no LIMIT 8",
            (company_id,),
        ).fetchall()

    tables = {}
    preferred_sections = [
        "재무상태표",
        "손익계산서",
        "포괄손익계산서",
        "주요재무지표",
        "안정성지표",
        "수익성지표",
        "성장성지표",
        "활동성지표",
        "현금흐름지표",
    ]
    for section in preferred_sections:
        if section in sections:
            payload = _financial_table_payload(company_id, section)
            if payload["periods"] and payload["rows"]:
                tables[section] = payload

    key_metrics = _key_metrics_payload(company_id)
    financial_statements = _financial_statements_payload(company_id)

    return JsonResponse(
        {
            "company": company,
            "health": health,
            "sections": sections,
            "notes": _dicts(notes),
            "tables": tables,
            "key_metrics": key_metrics,
            "financial_statements": financial_statements,
        }
    )


def _search_web(query: str) -> str:
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return "웹검색 API 키가 설정되지 않았습니다."

    client = TavilyClient(api_key=api_key)
    results = client.search(query=query, max_results=5)
    parts = []
    for result in results.get("results", []):
        parts.append(
            f"제목: {result.get('title', '')}\n"
            f"내용: {result.get('content', '')}\n"
            f"출처: {result.get('url', '')}"
        )
    return "\n\n".join(parts) if parts else "검색 결과가 없습니다."


def _build_company_context(company_id: int) -> str:
    with get_db() as conn:
        company = conn.execute(
            "SELECT company_name, representatives, biz_no, report_date "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
        if not company:
            return ""

        context_parts = [
            f"회사명: {company['company_name']}",
            f"대표자: {company['representatives']}",
            f"사업자번호: {company['biz_no']}",
            f"보고일: {company['report_date']}",
            "",
        ]

        for section in INCOME_SECTIONS + ["재무상태표"]:
            rows = conn.execute(
                "SELECT metric, period, value_raw, value_num, unit "
                "FROM report_values "
                "WHERE import_id = ? AND section = ? AND submetric IS NULL ORDER BY row_no",
                (company_id, section),
            ).fetchall()
            if not rows:
                continue
            context_parts.append(f"[{section}]")
            for row in rows:
                if row["value_num"] is not None:
                    unit = f" ({row['unit']})" if row["unit"] else ""
                    context_parts.append(f"  {row['metric']} ({row['period']}): {row['value_raw']}{unit}")
            context_parts.append("")

    health = calculate_health(company_id)
    if health.get("domains"):
        context_parts.append("[재무건전성 지표]")
        context_parts.append(f"  기준기간: {health['period']}")
        context_parts.append(f"  종합등급: {health['grade']} ({health['total_score']}점)")
    return "\n".join(context_parts)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def chat(request):
    if request.method == "OPTIONS":
        return HttpResponse(status=204)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": True, "reply": "요청 형식이 올바르지 않습니다."}, status=400)

    message = (payload.get("message") or "").strip()
    company_id = payload.get("company_id")
    if not message:
        return JsonResponse({"error": True, "reply": "메시지를 입력해주세요."}, status=400)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return JsonResponse(
            {
                "error": True,
                "reply": "OPENAI_API_KEY가 설정되지 않아 AI 분석을 실행할 수 없습니다.",
            }
        )

    context = _build_company_context(company_id) if company_id else ""
    system_content = (
        "당신은 한국 기업 재무 분석 전문가입니다. 답변은 한국어로 하고, "
        "숫자와 근거 중심으로 설명하세요. 최신 뉴스가 필요하면 web_search 도구를 사용하세요."
    )
    if context:
        system_content += f"\n\n=== 기업 재무 데이터 ===\n{context}"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        tool_spec = {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "최신 뉴스, 업계 동향, 기업 공시가 필요할 때 사용합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message},
        ]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[tool_spec],
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.6,
        )
        assistant_message = response.choices[0].message
        reply = assistant_message.content

        if assistant_message.tool_calls:
            messages.append(assistant_message)
            for tool_call in assistant_message.tool_calls:
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    tool_result = _search_web(args["query"])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )
            followup = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1024,
                temperature=0.6,
            )
            reply = followup.choices[0].message.content
    except Exception as exc:
        reply = f"AI 분석 중 오류가 발생했습니다: {exc}"

    return JsonResponse({"reply": reply})
