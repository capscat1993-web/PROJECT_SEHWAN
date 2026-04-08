import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.services.financial_health import calculate_health

router = APIRouter()

_TAVILY_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "최신 뉴스, 업계 동향, 기업 공시, 재무 비교 데이터가 필요할 때 웹을 검색합니다. "
            "특정 기업의 최근 이슈, 업종 평균 지표, 경쟁사 비교 등에 활용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 쿼리 (한국어 권장)"}
            },
            "required": ["query"],
        },
    },
}


class ChatRequest(BaseModel):
    company_id: Optional[int] = None
    message: str


def _search_web(query: str) -> str:
    """Tavily로 웹 검색 후 포맷된 결과 반환."""
    from tavily import TavilyClient

    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "웹검색 API 키가 설정되지 않았습니다."

    client = TavilyClient(api_key=api_key)
    results = client.search(query=query, max_results=5)
    parts = []
    for r in results.get("results", []):
        parts.append(
            f"제목: {r.get('title', '')}\n"
            f"내용: {r.get('content', '')}\n"
            f"출처: {r.get('url', '')}"
        )
    return "\n\n".join(parts) if parts else "검색 결과가 없습니다."


def _build_company_context(company_id: int) -> str:
    """DB에서 기업 재무 데이터와 건전성 지표를 컨텍스트 문자열로 빌드."""
    with get_db() as conn:
        company = conn.execute(
            "SELECT company_name, representatives, biz_no, report_date "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
        if not company:
            return ""

        sections = ["재무상태표", "손익계산서", "포괄손익계산서"]
        context_parts = [
            f"회사명: {company['company_name']}",
            f"대표자: {company['representatives']}",
            f"사업자번호: {company['biz_no']}",
            f"보고일: {company['report_date']}",
            "",
        ]

        for section in sections:
            rows = conn.execute(
                "SELECT metric, period, value_raw, value_num, unit "
                "FROM report_values "
                "WHERE import_id = ? AND section = ? AND submetric IS NULL "
                "ORDER BY row_no",
                (company_id, section),
            ).fetchall()
            if rows:
                context_parts.append(f"[{section}]")
                for r in rows:
                    if r["value_num"] is not None:
                        unit = f" ({r['unit']})" if r["unit"] else ""
                        context_parts.append(
                            f"  {r['metric']} ({r['period']}): {r['value_raw']}{unit}"
                        )
                context_parts.append("")

    health = calculate_health(company_id)
    if health.get("ratios"):
        context_parts.append("[재무건전성 지표]")
        context_parts.append(f"  기준기간: {health['period']}")
        for k, v in health["ratios"].items():
            context_parts.append(f"  {k}: {v}")
        context_parts.append(f"  종합등급: {health['grade']} ({health['average_score']}점)")

    return "\n".join(context_parts)


@router.post("/api/chat")
async def chat(req: ChatRequest):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {
            "reply": "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.",
            "error": True,
        }

    context = ""
    if req.company_id is not None:
        context = _build_company_context(req.company_id)
        if not context:
            raise HTTPException(status_code=404, detail="기업 정보를 찾을 수 없습니다.")

    system_content = (
        "당신은 한국 기업 재무 분석 전문가입니다. "
        "재무 건전성 평가, 투자 의견, 위험 요소, 업계 동향 등을 분석적으로 답변하세요. "
        "최신 뉴스, 업계 평균 비교, 기업 공시 등 외부 정보가 필요하면 web_search 도구를 사용하세요. "
        "답변은 한국어로 하세요."
    )
    if context:
        system_content += f"\n\n=== 기업 재무 데이터 ===\n{context}"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": req.message},
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[_TAVILY_TOOL],
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.7,
        )

        assistant_msg = response.choices[0].message

        if assistant_msg.tool_calls:
            messages.append(assistant_msg)
            for tool_call in assistant_msg.tool_calls:
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = _search_web(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result,
                    })
            response2 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            reply = response2.choices[0].message.content
        else:
            reply = assistant_msg.content

    except ImportError:
        reply = "openai 패키지가 설치되지 않았습니다. pip install openai 를 실행해주세요."
    except Exception as e:
        reply = f"API 호출 오류: {str(e)}"

    return {"reply": reply}
