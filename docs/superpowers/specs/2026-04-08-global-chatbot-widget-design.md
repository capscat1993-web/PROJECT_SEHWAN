# 전역 플로팅 챗봇 위젯 + Tavily 웹검색 설계

**날짜:** 2026-04-08  
**상태:** 승인됨

---

## 개요

기존 기업 상세 페이지의 "AI 분석" 탭을 제거하고, 전체 페이지에서 접근 가능한 **우측 하단 플로팅 챗봇 위젯**으로 대체한다. 챗봇은 기업 상세 페이지에서는 해당 기업의 재무 데이터를 자동으로 컨텍스트에 포함하고, 메인 페이지에서는 웹검색 기반 범용 재무 상담 모드로 동작한다. Tavily API를 통해 AI가 필요 시 웹검색을 수행한다.

---

## 아키텍처

### 백엔드 (`app/routers/chat.py`)

- `ChatRequest.company_id`를 `Optional[int]`로 변경
- OpenAI Function Calling에 `web_search` 도구 등록
  - AI가 최신 뉴스, 업계 비교, 공시 등 외부 정보가 필요하다고 판단할 때 자동 호출
  - Tavily Python SDK(`tavily-python`)로 검색 실행
  - 검색 결과를 추가 메시지로 삽입 후 최종 답변 생성
- `company_id` 있을 때: DB 재무 데이터 + 재무건전성 8개 지표 컨텍스트 주입
- `company_id` 없을 때: 시스템 프롬프트만 적용 (웹검색 가능)
- 환경 변수 `TAVILY_API_KEY` 사용

### 프론트엔드

**`app/templates/base.html`**
- 모든 페이지 하단에 플로팅 위젯 HTML/CSS/JS 삽입
- 우측 하단 고정 버튼(💬) 클릭 시 채팅 패널 슬라이드업
- `window.CID` 존재 여부로 기업 컨텍스트 자동 감지
  - 기업 페이지: `CID` 포함하여 `/api/chat` 호출
  - 메인 페이지: `company_id` 없이 호출
- 접기/펼치기 상태 CSS 트랜지션으로 처리

**`app/templates/company.html`**
- "AI 분석" 탭 버튼 제거
- `tab-chat` div 제거
- `initChat()` 함수 제거
- `CID` 변수는 유지 (위젯이 참조)

**`requirements.txt`**
- `tavily-python` 추가

---

## 데이터 흐름

```
사용자 메시지 입력
  → 프론트엔드: window.CID 확인
    → CID 있음: POST /api/chat { company_id, message }
    → CID 없음: POST /api/chat { message }
  → 백엔드: company_id 있으면 DB 컨텍스트 빌드
  → OpenAI API 호출 (tools: [web_search])
    → AI가 웹검색 필요 판단 시: Tavily 호출 → 결과 삽입 → 재호출
    → 웹검색 불필요 시: 바로 답변 생성
  → 최종 답변 프론트엔드 반환
```

---

## 환경 변수

| 변수명 | 용도 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI API 인증 (기존) |
| `TAVILY_API_KEY` | Tavily 웹검색 API 인증 (신규) |

---

## 범위 외 (이번 구현 제외)

- 대화 히스토리 서버 저장 (세션 내 메모리만 유지)
- 다중 기업 비교 기능
- 챗봇 로그 기록
