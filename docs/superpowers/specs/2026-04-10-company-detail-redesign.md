# 회사 상세페이지 리디자인 스펙

**날짜:** 2026-04-10  
**참고 레퍼런스:** https://dartpoint.ai/00155124

---

## 목표

dartpoint.ai 스타일의 파란색/흰색 기업형 UI로 전환하고, 탭 기반 재무제표 섹션을 추가한다.

---

## 색상/테마

| 변수 | 변경 후 |
|---|---|
| `--bg` | `#f1f5f9` |
| `--surface` | `#ffffff` |
| `--surface-strong` | `#f8fafc` |
| `--text` | `#0f172a` |
| `--muted` | `#64748b` |
| `--line` | `rgba(0,0,0,0.08)` |
| `--accent` | `#2563eb` |
| `--accent-2` | `#0ea5e9` |
| `--accent-3` | `#10b981` |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.08)` |

- 배경 방사형 그라디언트 제거 → 단색 `#f1f5f9`
- Glassmorphism 제거 (`backdrop-filter`, 반투명 배경 없앰)
- 카드: 흰색 배경 + `border: 1px solid #e2e8f0`
- body background: `#f1f5f9`

---

## 레이아웃 구조

### 1. 헤더 바 (`detail-hero`)

현재 좌우 2컬럼 분할 → 상단 가로 바 형태로 변경

```
← 전체 목록  [회사명]  [업종 배지]  [주요제품 배지]
대표자: OOO · 사업자번호: OOO · 보고일: OOO
```

- 흰색 배경, `border-bottom: 1px solid #e2e8f0`
- 회사명: `h1` 1.8rem, font-weight 700
- 업종/주요제품: pill badge (`background: #eff6ff`, `color: #2563eb`)
- 메타 정보: `·` 구분자로 한 줄 표시

### 2. 주요 패널 그리드

```
[재무건전성 패널 (0.95fr)] [핵심 실적 지표 (1.05fr)]
```

**재무건전성 패널 변경:**
- 등급 배지: `#2563eb` 배경, 흰색 텍스트
- 도메인 progress bar: 파란색 계열 (`#2563eb` → `#7dd3fc`)
- 의견 텍스트 블록: `#f8fafc` 배경

**핵심 실적 지표 패널:**
- 수평 bar 유지, 색상 파란색 계열 전환

### 3. 탭 기반 재무제표 (신규)

새 클라이언트 컴포넌트 `FinancialTabs` 추가.

- **탭 목록:** `tables` 객체의 section 키를 자동으로 탭 생성
- **기간 필터:** `[1년] [3년] [5년]` 버튼 — 프론트에서 periods 최근 N개 필터링
- **엑셀 다운로드:** 기존 health export와 동일 패턴 링크 버튼
- **탭 스타일:** 선택된 탭 `border-bottom: 2px solid #2563eb`, 나머지 회색
- **테이블 스타일:**
  - `th`: `#f8fafc` 배경, `0.82rem`, 대문자
  - 숫자: 우측 정렬, `font-variant-numeric: tabular-nums`
  - hover row: `#f1f5f9`

### 4. 특이사항 노트

하단 단독 섹션으로 이동 (기존 위치에서 분리)

---

## 파일 변경 범위

| 파일 | 변경 내용 |
|---|---|
| `frontend/src/app/globals.css` | 색상 변수, 배경, glassmorphism 제거, 카드 스타일 |
| `frontend/src/app/company/[companyId]/page.tsx` | 헤더 바 구조 변경, FinancialTabs 추가 |
| `frontend/src/components/health-panel.tsx` | 배지/바 색상 업데이트 |
| `frontend/src/components/financial-tabs.tsx` | 신규 — 탭+기간필터+테이블 |

---

## 범위 외

- 백엔드 API 변경 없음
- 기간 필터는 프론트에서 처리 (이미 받은 데이터 슬라이싱)
- 차트 라이브러리 추가 없음 (bar 방식 유지)
