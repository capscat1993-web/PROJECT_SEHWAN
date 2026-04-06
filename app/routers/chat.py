import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.services.financial_health import calculate_health

router = APIRouter()


class ChatRequest(BaseModel):
    company_id: int
    message: str


def _build_company_context(company_id: int) -> str:
    """Build financial context string for the AI prompt."""
    with get_db() as conn:
        company = conn.execute(
            "SELECT company_name, representatives, biz_no, report_date "
            "FROM report_imports WHERE id = ?",
            (company_id,),
        ).fetchone()
        if not company:
            return ""

        # Get key financial data
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
                        context_parts.append(f"  {r['metric']} ({r['period']}): {r['value_raw']}{unit}")
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

    context = _build_company_context(req.company_id)
    if not context:
        raise HTTPException(status_code=404, detail="기업 정보를 찾을 수 없습니다.")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 한국 기업 재무 분석 전문가입니다. "
                        "아래 기업의 재무 데이터를 기반으로 질문에 답변하세요. "
                        "재무 건전성 평가, 투자 의견, 위험 요소 등을 분석적으로 답변하세요. "
                        "답변은 한국어로 하세요.\n\n"
                        f"=== 기업 재무 데이터 ===\n{context}"
                    ),
                },
                {"role": "user", "content": req.message},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
    except ImportError:
        reply = "openai 패키지가 설치되지 않았습니다. pip install openai 를 실행해주세요."
    except Exception as e:
        reply = f"API 호출 오류: {str(e)}"

    return {"reply": reply}
