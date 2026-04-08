# 전역 플로팅 챗봇 위젯 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기업 상세 페이지의 AI 분석 탭을 제거하고, 전체 페이지에서 접근 가능한 우측 하단 플로팅 챗봇 위젯으로 대체한다. 기업 페이지에서는 해당 기업 재무 데이터를 자동으로 주입하고, 메인 페이지에서는 Tavily 웹검색 기반 범용 모드로 동작한다.

**Architecture:** FastAPI 백엔드의 `/api/chat` 엔드포인트를 company_id Optional로 변경하고 OpenAI Function Calling으로 Tavily 웹검색 도구를 등록한다. base.html에 전역 플로팅 위젯을 추가하고, company.html에서 기존 AI 분석 탭을 제거한다.

**Tech Stack:** Python/FastAPI, OpenAI gpt-4o-mini (Function Calling), Tavily Python SDK, Jinja2, Tailwind CSS (CDN)

---

## 파일 맵

| 파일 | 변경 유형 | 역할 |
|------|-----------|------|
| `requirements.txt` | 수정 | `tavily-python` 추가 |
| `app/routers/chat.py` | 수정 | company_id Optional화, Tavily 함수 호출 통합 |
| `app/templates/base.html` | 수정 | 전역 플로팅 위젯 HTML/CSS/JS 추가 |
| `app/templates/company.html` | 수정 | AI 분석 탭 제거, initChat/sendChat 함수 제거 |
| `tests/test_chat.py` | 생성 | chat 라우터 단위 테스트 |

---

## Task 1: tavily-python 패키지 추가

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: requirements.txt에 tavily-python 추가**

```text
pandas
openpyxl
pypdf
fastapi
uvicorn[standard]
jinja2
python-dotenv
openai
tavily-python
```

- [ ] **Step 2: 패키지 설치 확인**

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed tavily-python-...` 또는 `already satisfied`

- [ ] **Step 3: Tavily import 동작 확인**

```bash
python -c "from tavily import TavilyClient; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: 커밋**

```bash
git add requirements.txt
git commit -m "feat: add tavily-python dependency"
```

---

## Task 2: chat.py 백엔드 업데이트

**Files:**
- Modify: `app/routers/chat.py`
- Create: `tests/test_chat.py`

- [ ] **Step 1: 테스트 파일 작성**

`tests/test_chat.py` 전체 내용:

```python
"""chat 라우터 단위 테스트."""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestChatRequest:
    def test_chat_without_company_id_returns_200(self):
        """company_id 없이 호출 시 422가 아닌 정상 응답."""
        mock_choice = MagicMock()
        mock_choice.message.content = "테스트 답변"
        mock_choice.message.tool_calls = None

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("app.routers.chat.os.environ.get", side_effect=lambda k, d="": {
            "OPENAI_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-tavily",
        }.get(k, d)):
            with patch("openai.OpenAI") as mock_openai:
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                res = client.post("/api/chat", json={"message": "재무 건전성이란?"})

        assert res.status_code == 200
        assert "reply" in res.json()

    def test_chat_with_invalid_company_id_returns_404(self):
        """존재하지 않는 company_id 사용 시 404 반환."""
        with patch("app.routers.chat.os.environ.get", return_value="test-key"):
            res = client.post("/api/chat", json={"company_id": 999999, "message": "분석해줘"})

        assert res.status_code == 404

    def test_missing_message_returns_422(self):
        """message 누락 시 422 반환."""
        res = client.post("/api/chat", json={"company_id": 1})
        assert res.status_code == 422


class TestSearchWeb:
    def test_search_web_returns_formatted_string(self):
        """_search_web가 검색 결과를 포맷된 문자열로 반환."""
        from app.routers.chat import _search_web

        mock_results = {
            "results": [
                {"title": "현대차 2025 실적", "content": "영업이익 증가", "url": "https://example.com"},
            ]
        }
        with patch("app.routers.chat.os.environ.get", return_value="test-key"):
            with patch("tavily.TavilyClient") as mock_tavily:
                mock_tavily.return_value.search.return_value = mock_results
                result = _search_web("현대차 최근 뉴스")

        assert "현대차 2025 실적" in result
        assert "영업이익 증가" in result
        assert "https://example.com" in result

    def test_search_web_no_api_key(self):
        """TAVILY_API_KEY 없을 때 에러 메시지 반환."""
        from app.routers.chat import _search_web

        with patch("app.routers.chat.os.environ.get", return_value=""):
            result = _search_web("테스트")

        assert "API 키" in result
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
cd C:/Users/user/Desktop/PROJECT_SEHWAN
python -m pytest tests/test_chat.py -v 2>&1 | head -40
```

Expected: FAILED (chat.py에 `_search_web` 없고 company_id 필수라 에러)

- [ ] **Step 3: chat.py 전체 교체**

`app/routers/chat.py` 전체 내용:

```python
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
```

- [ ] **Step 4: 테스트 재실행 → 통과 확인**

```bash
python -m pytest tests/test_chat.py -v
```

Expected: 5개 테스트 모두 PASSED

- [ ] **Step 5: 커밋**

```bash
git add app/routers/chat.py tests/test_chat.py
git commit -m "feat: make company_id optional and add Tavily web search via function calling"
```

---

## Task 3: base.html 전역 플로팅 위젯 추가

**Files:**
- Modify: `app/templates/base.html`

- [ ] **Step 1: base.html의 `</body>` 직전에 위젯 삽입**

`{% block scripts %}{% endblock %}` 바로 아래, `</body>` 바로 위에 다음 코드를 추가:

```html
  <!-- ─── 전역 플로팅 챗봇 위젯 ─────────────────────────────── -->
  <div id="chatWidget" style="position:fixed;bottom:24px;right:24px;z-index:1000;display:flex;flex-direction:column;align-items:flex-end;">
    <!-- 채팅 패널 -->
    <div id="chatPanel"
      style="display:none;width:360px;height:500px;background:#fff;border-radius:16px;
             box-shadow:0 8px 32px rgba(0,0,0,0.18);flex-direction:column;overflow:hidden;
             margin-bottom:12px;border:1px solid #e5e7eb;">
      <!-- 헤더 -->
      <div style="padding:14px 16px;background:#2563eb;color:#fff;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
        <div>
          <div style="font-weight:600;font-size:14px;">AI 재무 분석</div>
          <div id="widgetSubtitle" style="font-size:11px;opacity:0.75;margin-top:2px;">재무·업계 질문에 답변합니다</div>
        </div>
        <button onclick="toggleChat()"
          style="background:none;border:none;color:#fff;cursor:pointer;font-size:20px;line-height:1;padding:0 4px;">×</button>
      </div>
      <!-- 메시지 영역 -->
      <div id="widgetMessages"
        style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f8fafc;">
        <div style="background:#eff6ff;color:#1e40af;border-radius:10px;padding:10px 13px;font-size:13px;line-height:1.5;">
          안녕하세요! 재무 건전성, 최신 뉴스, 업계 동향 등을 질문해주세요.<br>
          <span style="opacity:0.7;font-size:11px;">예: "이 기업 부채비율이 높은 이유는?", "자동차부품 업계 평균 영업이익률은?"</span>
        </div>
      </div>
      <!-- 입력 영역 -->
      <div style="padding:10px 12px;border-top:1px solid #e5e7eb;display:flex;gap:8px;flex-shrink:0;background:#fff;">
        <input id="widgetInput" type="text" placeholder="질문을 입력하세요..."
          style="flex:1;border:1px solid #d1d5db;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;
                 transition:border-color 0.15s;"
          onfocus="this.style.borderColor='#2563eb'" onblur="this.style.borderColor='#d1d5db'"
          onkeydown="if(event.key==='Enter')sendWidgetChat()">
        <button onclick="sendWidgetChat()"
          style="background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 16px;
                 font-size:13px;cursor:pointer;white-space:nowrap;transition:background 0.15s;"
          onmouseover="this.style.background='#1d4ed8'" onmouseout="this.style.background='#2563eb'">전송</button>
      </div>
    </div>
    <!-- 토글 버튼 -->
    <button id="chatToggleBtn" onclick="toggleChat()"
      style="width:56px;height:56px;border-radius:50%;background:#2563eb;color:#fff;border:none;
             cursor:pointer;box-shadow:0 4px 16px rgba(37,99,235,0.4);font-size:22px;
             display:flex;align-items:center;justify-content:center;transition:transform 0.15s;"
      onmouseover="this.style.transform='scale(1.08)'" onmouseout="this.style.transform='scale(1)'">
      💬
    </button>
  </div>

  <script>
  (function () {
    function toggleChat() {
      var panel = document.getElementById('chatPanel');
      var isOpen = panel.style.display === 'flex';
      panel.style.display = isOpen ? 'none' : 'flex';
      if (!isOpen) document.getElementById('widgetInput').focus();
    }
    window.toggleChat = toggleChat;

    // 기업 페이지에서 회사명을 서브타이틀에 반영
    window.addEventListener('load', function () {
      if (typeof window.CID !== 'undefined' && window.CID) {
        var sub = document.getElementById('widgetSubtitle');
        if (sub) sub.textContent = '이 기업의 재무 데이터를 기반으로 분석합니다';
      }
    });

    async function sendWidgetChat() {
      var input = document.getElementById('widgetInput');
      var msg = input.value.trim();
      if (!msg) return;

      var messages = document.getElementById('widgetMessages');

      // 사용자 메시지
      var userDiv = document.createElement('div');
      userDiv.style.cssText = 'background:#f3f4f6;border-radius:10px;padding:10px 13px;font-size:13px;align-self:flex-end;max-width:82%;line-height:1.5;word-break:break-word;';
      userDiv.textContent = msg;
      messages.appendChild(userDiv);
      input.value = '';
      messages.scrollTop = messages.scrollHeight;

      // 로딩
      var loadDiv = document.createElement('div');
      var lid = 'ld-' + Date.now();
      loadDiv.id = lid;
      loadDiv.style.cssText = 'background:#f1f5f9;border-radius:10px;padding:10px 13px;font-size:13px;color:#94a3b8;';
      loadDiv.textContent = '분석 중...';
      messages.appendChild(loadDiv);
      messages.scrollTop = messages.scrollHeight;

      var body = { message: msg };
      if (typeof window.CID !== 'undefined' && window.CID) body.company_id = window.CID;

      try {
        var res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        var data = await res.json();
        var ld = document.getElementById(lid);
        if (ld) ld.remove();

        var replyDiv = document.createElement('div');
        if (data.error) {
          replyDiv.style.cssText = 'background:#fef2f2;color:#b91c1c;border-radius:10px;padding:10px 13px;font-size:13px;line-height:1.5;white-space:pre-wrap;';
        } else {
          replyDiv.style.cssText = 'background:#eff6ff;color:#1e3a8a;border-radius:10px;padding:10px 13px;font-size:13px;line-height:1.5;white-space:pre-wrap;';
        }
        replyDiv.textContent = data.reply;
        messages.appendChild(replyDiv);
      } catch (e) {
        var ld2 = document.getElementById(lid);
        if (ld2) ld2.remove();
        var errDiv = document.createElement('div');
        errDiv.style.cssText = 'background:#fef2f2;color:#b91c1c;border-radius:10px;padding:10px 13px;font-size:13px;';
        errDiv.textContent = '오류가 발생했습니다.';
        messages.appendChild(errDiv);
      }
      messages.scrollTop = messages.scrollHeight;
    }
    window.sendWidgetChat = sendWidgetChat;
  })();
  </script>
```

- [ ] **Step 2: 서버 재시작 후 메인 페이지에서 위젯 확인**

```bash
uvicorn app.main:app --reload --port 8000
```

브라우저에서 `http://localhost:8000` 접속 → 우측 하단 💬 버튼 표시 확인 → 클릭 시 패널 펼침 확인

- [ ] **Step 3: 커밋**

```bash
git add app/templates/base.html
git commit -m "feat: add global floating chat widget to base.html"
```

---

## Task 4: company.html AI 분석 탭 제거

**Files:**
- Modify: `app/templates/company.html`

- [ ] **Step 1: AI 분석 탭 버튼 제거**

`company.html` 23~27행 근처에서 아래 줄 삭제:

```html
      <button onclick="switchTab('chat')" data-tab="chat" class="py-2 text-sm text-gray-500 hover:text-gray-700">AI 분석</button>
```

- [ ] **Step 2: tab-chat div 제거**

아래 줄 삭제:

```html
  <div id="tab-chat" class="tab-content hidden"></div>
```

- [ ] **Step 3: switchTab 함수에서 chat 분기 제거**

`switchTab` 함수 내 아래 줄 삭제:

```javascript
  if (tab === 'chat' && !document.getElementById('tab-chat').dataset.loaded) initChat();
```

- [ ] **Step 4: initChat 함수 전체 삭제**

아래 블록 전체 삭제 (company.html 761~787행):

```javascript
// ─── AI 챗봇 탭 ──────────────────────────────────────────
function initChat() {
  const tab = document.getElementById('tab-chat');
  tab.dataset.loaded = '1';
  tab.innerHTML = `
    ...
  `;
}
```

- [ ] **Step 5: sendChat 함수 전체 삭제**

아래 블록 전체 삭제 (company.html 789~815행):

```javascript
async function sendChat() {
  ...
}
```

- [ ] **Step 6: 동작 확인**

브라우저에서 기업 상세 페이지 접속 → "AI 분석" 탭 없음 확인 → 플로팅 위젯에서 기업 이름 서브타이틀 반영 확인 → 질문 입력 시 재무 데이터 기반 답변 확인

- [ ] **Step 7: 커밋**

```bash
git add app/templates/company.html
git commit -m "refactor: remove AI 분석 tab from company page, replaced by global floating widget"
```

---

## Task 5: 웹검색 통합 E2E 확인

- [ ] **Step 1: 메인 페이지에서 업계 질문 테스트**

브라우저에서 메인 페이지(`/`) → 플로팅 위젯 열기 → 아래 질문 입력:

```
자동차부품 업계 평균 부채비율은 어느 정도인가요?
```

Expected: Tavily 웹검색 결과를 반영한 답변 (업계 데이터 포함)

- [ ] **Step 2: 기업 페이지에서 뉴스 + 재무 복합 질문 테스트**

기업 상세 페이지 → 플로팅 위젯 → 아래 질문 입력:

```
이 기업의 최근 뉴스와 재무 건전성을 종합적으로 분석해줘
```

Expected: DB 재무 데이터 + Tavily 검색 결과를 모두 반영한 답변

- [ ] **Step 3: 최종 커밋 (필요 시)**

```bash
git add -A
git commit -m "feat: global floating chatbot with Tavily web search complete"
```
