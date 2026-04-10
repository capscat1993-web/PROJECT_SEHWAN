# Company Detail Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 회사 상세페이지를 dartpoint.ai 스타일의 파란색/흰색 기업형 UI로 재디자인하고, 탭 기반 재무제표 섹션을 추가한다.

**Architecture:** globals.css의 색상 변수와 레이아웃 클래스를 직접 수정해 전체 테마를 전환하고, 기존 `SectionTable` 나열 방식을 `FinancialTabs` 클라이언트 컴포넌트로 대체한다. 백엔드 API 변경 없이 프론트에서만 처리.

**Tech Stack:** Next.js 14 (App Router), React, TypeScript, CSS (globals.css)

---

## 파일 변경 목록

| 파일 | 역할 |
|---|---|
| `frontend/src/app/globals.css` | 색상 변수, body 배경, glassmorphism 제거, 카드/헤더 스타일 |
| `frontend/src/components/dashboard-shell.tsx` | background orb 제거 |
| `frontend/src/app/company/[companyId]/page.tsx` | 헤더 바 구조, FinancialTabs + NotesPanel 배치 |
| `frontend/src/components/health-panel.tsx` | grade-badge, score-bar 색상 파란색 전환 |
| `frontend/src/components/financial-tabs.tsx` | 신규 — 탭+기간필터+테이블 |

---

## Task 1: globals.css — 색상 변수 및 body 배경 전환

**Files:**
- Modify: `frontend/src/app/globals.css:1-31`

- [ ] **Step 1: CSS 변수 및 body 배경 교체**

`:root` 블록과 `body` 스타일을 아래로 교체한다.

```css
:root {
  --bg: #f1f5f9;
  --surface: #ffffff;
  --surface-strong: #f8fafc;
  --text: #0f172a;
  --muted: #64748b;
  --line: rgba(0, 0, 0, 0.08);
  --accent: #2563eb;
  --accent-2: #0ea5e9;
  --accent-3: #10b981;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
}
```

`body` 스타일을 아래로 교체한다.

```css
body {
  margin: 0;
  color: var(--text);
  background: var(--bg);
  font-family: "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}
```

- [ ] **Step 2: Glassmorphism 제거 — 카드 공통 스타일**

아래 셀렉터 블록을 찾는다.

```css
.hero-panel,
.detail-hero,
.panel,
.metric-card,
.company-card,
.mini-company-card,
.spotlight-card,
.detail-meta-card,
.section-card,
.note-card,
.domain-card,
.series-card {
  backdrop-filter: blur(18px);
  background: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: var(--shadow);
}
```

아래로 교체한다.

```css
.hero-panel,
.detail-hero,
.panel,
.metric-card,
.company-card,
.mini-company-card,
.spotlight-card,
.detail-meta-card,
.section-card,
.note-card,
.domain-card,
.series-card {
  background: var(--surface);
  border: 1px solid #e2e8f0;
  box-shadow: var(--shadow);
}
```

- [ ] **Step 3: background-orb 클래스 제거**

아래 블록 전체를 삭제한다.

```css
.background-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(12px);
  opacity: 0.55;
}

.background-orb-a {
  width: 24rem;
  height: 24rem;
  background: rgba(217, 107, 59, 0.18);
  top: -8rem;
  right: -5rem;
}

.background-orb-b {
  width: 18rem;
  height: 18rem;
  background: rgba(13, 124, 134, 0.18);
  left: -4rem;
  bottom: 8rem;
}
```

- [ ] **Step 4: detail-hero를 가로 바 레이아웃으로 변경**

현재 `.hero-panel, .detail-hero` 블록을 찾는다.

```css
.hero-panel,
.detail-hero {
  display: grid;
  grid-template-columns: 1.35fr 0.95fr;
  gap: 24px;
  align-items: stretch;
  padding: 32px;
  border-radius: 32px;
  margin-bottom: 24px;
}
```

아래로 교체한다.

```css
.hero-panel {
  display: grid;
  grid-template-columns: 1.35fr 0.95fr;
  gap: 24px;
  align-items: stretch;
  padding: 32px;
  border-radius: 32px;
  margin-bottom: 24px;
}

.detail-hero {
  display: block;
  padding: 24px 28px;
  border-radius: 16px;
  margin-bottom: 20px;
}
```

- [ ] **Step 5: detail-hero 내부 스타일 추가**

파일 하단(미디어 쿼리 위)에 아래를 추가한다.

```css
.detail-hero-top {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.detail-hero-top h1 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.detail-hero-meta {
  display: flex;
  gap: 0;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 0.9rem;
}

.detail-hero-meta span + span::before {
  content: " · ";
  margin: 0 6px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 600;
}

.financial-tabs-wrap {
  background: var(--surface);
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  margin-bottom: 20px;
  overflow: hidden;
}

.financial-tabs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #e2e8f0;
  gap: 12px;
  flex-wrap: wrap;
}

.financial-tab-list {
  display: flex;
  gap: 0;
}

.financial-tab-btn {
  padding: 14px 18px;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 120ms, border-color 120ms;
}

.financial-tab-btn:hover {
  color: var(--text);
}

.financial-tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 700;
}

.financial-tab-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
}

.period-btn {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: transparent;
  font-size: 0.82rem;
  color: var(--muted);
  cursor: pointer;
  transition: background 120ms, color 120ms, border-color 120ms;
}

.period-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.financial-tab-body {
  padding: 0;
}

.financial-tab-body .table-wrap {
  margin: 0;
}

.financial-tab-body th {
  background: var(--surface-strong);
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
}

.financial-tab-body td:not(:first-child),
.financial-tab-body th:not(:first-child) {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.financial-tab-body tbody tr:hover td {
  background: #f1f5f9;
}
```

- [ ] **Step 6: grade-badge 색상 파란색으로 수정**

아래를 찾아서:

```css
.grade-badge {
  width: 92px;
  height: 92px;
  border-radius: 28px;
  background: linear-gradient(135deg, var(--accent), #ef946c);
  color: white;
  display: grid;
  place-items: center;
  font-size: 2rem;
  font-weight: 800;
}
```

아래로 교체한다.

```css
.grade-badge {
  width: 92px;
  height: 92px;
  border-radius: 28px;
  background: linear-gradient(135deg, #2563eb, #60a5fa);
  color: white;
  display: grid;
  place-items: center;
  font-size: 2rem;
  font-weight: 800;
}
```

- [ ] **Step 7: score-bar 색상 파란색으로 수정**

아래를 찾아서:

```css
.score-bar > div {
  background: linear-gradient(90deg, var(--accent-3), #87d0b1);
}
```

아래로 교체한다.

```css
.score-bar > div {
  background: linear-gradient(90deg, #2563eb, #7dd3fc);
}
```

- [ ] **Step 8: health-topline 배경 파란색 계열로 수정**

아래를 찾아서:

```css
.health-topline {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 18px;
  align-items: center;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(217, 107, 59, 0.1), rgba(255, 255, 255, 0.66));
}
```

아래로 교체한다.

```css
.health-topline {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 18px;
  align-items: center;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(248, 250, 252, 0.9));
}
```

- [ ] **Step 9: eyebrow 색상 파란색으로 수정**

아래를 찾아서:

```css
.eyebrow {
  display: inline-flex;
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent-2);
  font-weight: 700;
}
```

아래로 교체한다.

```css
.eyebrow {
  display: inline-flex;
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
}
```

- [ ] **Step 10: series-fill 색상 파란색으로 수정**

아래를 찾아서:

```css
.series-fill {
  background: linear-gradient(90deg, var(--accent-2), #7fd0d7);
}
```

아래로 교체한다.

```css
.series-fill {
  background: linear-gradient(90deg, #2563eb, #93c5fd);
}
```

- [ ] **Step 11: ghost-button 색상 파란색으로 수정**

아래를 찾아서:

```css
.ghost-button {
  background: rgba(217, 107, 59, 0.12);
  color: var(--accent);
}
```

아래로 교체한다.

```css
.ghost-button {
  background: rgba(37, 99, 235, 0.08);
  color: var(--accent);
}
```

- [ ] **Step 12: search-bar 버튼 색상 파란색으로 수정**

아래를 찾아서:

```css
.search-bar button {
  background: linear-gradient(135deg, var(--accent), #ef946c);
  color: white;
}
```

아래로 교체한다.

```css
.search-bar button {
  background: linear-gradient(135deg, #2563eb, #60a5fa);
  color: white;
}
```

- [ ] **Step 13: back-link 색상 파란색으로 수정**

아래를 찾아서:

```css
.back-link {
  display: inline-flex;
  margin-bottom: 18px;
  color: var(--accent);
  font-weight: 700;
}
```

아래로 교체한다.

```css
.back-link {
  display: inline-flex;
  margin-bottom: 14px;
  color: var(--accent);
  font-size: 0.88rem;
  font-weight: 600;
}
```

- [ ] **Step 14: note-card span 색상 파란색으로 수정**

아래를 찾아서:

```css
.note-card span {
  display: inline-flex;
  margin-bottom: 8px;
  color: var(--accent-2);
  font-weight: 700;
}
```

아래로 교체한다.

```css
.note-card span {
  display: inline-flex;
  margin-bottom: 8px;
  color: var(--accent);
  font-weight: 700;
}
```

- [ ] **Step 15: tag 색상 파란색으로 수정**

아래를 찾아서:

```css
.tag {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  padding: 7px 12px;
  background: rgba(13, 124, 134, 0.12);
  color: var(--accent-2);
  font-size: 0.82rem;
  font-weight: 700;
}
```

아래로 교체한다.

```css
.tag {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  padding: 7px 12px;
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
}
```

- [ ] **Step 16: detail-hero h1 스타일 덮어쓰기 제거**

아래를 찾아서:

```css
.hero-copy h1,
.detail-hero h1 {
  margin: 10px 0 14px;
  font-size: clamp(2.3rem, 4vw, 4.5rem);
  line-height: 0.96;
  letter-spacing: -0.05em;
}
```

아래로 교체한다.

```css
.hero-copy h1 {
  margin: 10px 0 14px;
  font-size: clamp(2.3rem, 4vw, 4.5rem);
  line-height: 0.96;
  letter-spacing: -0.05em;
}
```

- [ ] **Step 17: 커밋**

```bash
git add frontend/src/app/globals.css
git commit -m "style: migrate to blue/white corporate theme, remove glassmorphism"
```

---

## Task 2: dashboard-shell.tsx — background orb 제거

**Files:**
- Modify: `frontend/src/components/dashboard-shell.tsx`

- [ ] **Step 1: orb div 제거**

파일 전체를 아래로 교체한다.

```tsx
export function DashboardShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="page-shell">
      <main className="page-content">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: 커밋**

```bash
git add frontend/src/components/dashboard-shell.tsx
git commit -m "style: remove background orbs from dashboard shell"
```

---

## Task 3: financial-tabs.tsx — 신규 탭+기간필터 컴포넌트

**Files:**
- Create: `frontend/src/components/financial-tabs.tsx`

- [ ] **Step 1: 컴포넌트 생성**

```tsx
"use client";

import { useState } from "react";

type TableData = {
  section: string;
  periods: string[];
  unit: string;
  rows: {
    metric: string;
    values: Record<string, { raw: string; num: number | null }>;
  }[];
};

export function FinancialTabs({
  tables,
  companyId,
}: Readonly<{
  tables: Record<string, TableData>;
  companyId: number;
}>) {
  const sections = Object.keys(tables);
  const [activeTab, setActiveTab] = useState(sections[0] ?? "");
  const [periodYears, setPeriodYears] = useState<1 | 3 | 5>(5);

  if (sections.length === 0) {
    return <div className="empty-card">재무 데이터가 없습니다.</div>;
  }

  const table = tables[activeTab];

  // 최근 N년치 periods 필터: periods는 연도 문자열 배열 (예: ["2020", "2021", "2022"])
  // 내림차순 정렬 후 앞 N개 선택, 다시 오름차순으로 표시
  const filteredPeriods = [...table.periods]
    .sort((a, b) => b.localeCompare(a))
    .slice(0, periodYears)
    .sort((a, b) => a.localeCompare(b));

  const exportUrl = `/api/companies/${companyId}/health/export`;

  return (
    <div className="financial-tabs-wrap">
      <div className="financial-tabs-header">
        <div className="financial-tab-list">
          {sections.map((section) => (
            <button
              key={section}
              className={`financial-tab-btn${activeTab === section ? " active" : ""}`}
              onClick={() => setActiveTab(section)}
            >
              {section}
            </button>
          ))}
        </div>

        <div className="financial-tab-controls">
          {([1, 3, 5] as const).map((y) => (
            <button
              key={y}
              className={`period-btn${periodYears === y ? " active" : ""}`}
              onClick={() => setPeriodYears(y)}
            >
              {y}년
            </button>
          ))}
          <a href={exportUrl} className="ghost-button" style={{ fontSize: "0.82rem", padding: "6px 14px" }}>
            엑셀↓
          </a>
        </div>
      </div>

      <div className="financial-tab-body">
        <div className="table-wrap">
          {table.unit && (
            <p style={{ margin: "12px 16px 4px", fontSize: "0.82rem", color: "var(--muted)" }}>
              단위: {table.unit}
            </p>
          )}
          <table>
            <thead>
              <tr>
                <th>지표</th>
                {filteredPeriods.map((period) => (
                  <th key={period}>{period}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row) => (
                <tr key={row.metric}>
                  <td>{row.metric}</td>
                  {filteredPeriods.map((period) => (
                    <td key={period}>{row.values[period]?.raw || "-"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 커밋**

```bash
git add frontend/src/components/financial-tabs.tsx
git commit -m "feat: add FinancialTabs component with period filter"
```

---

## Task 4: company/[companyId]/page.tsx — 헤더 바 + FinancialTabs 적용

**Files:**
- Modify: `frontend/src/app/company/[companyId]/page.tsx`

- [ ] **Step 1: import 추가 및 SectionTable import 제거**

파일 상단 import를 아래로 교체한다.

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";

import { DashboardShell } from "@/components/dashboard-shell";
import { FinancialTabs } from "@/components/financial-tabs";
import { HealthPanel } from "@/components/health-panel";
import { KeyMetricsPanel } from "@/components/key-metrics-panel";
import { NotesPanel } from "@/components/notes-panel";
import { apiFetch } from "@/lib/api";
```

- [ ] **Step 2: JSX 전체 교체**

`return (` 이하 전체를 아래로 교체한다.

```tsx
  return (
    <DashboardShell>
      {/* 헤더 바 */}
      <section className="detail-hero">
        <Link href="/" className="back-link">
          ← 전체 목록
        </Link>
        <div className="detail-hero-top">
          <h1>{company.company_name}</h1>
          {company.industry && <span className="badge">{company.industry}</span>}
          {company.main_product && <span className="badge">{company.main_product}</span>}
        </div>
        <div className="detail-hero-meta">
          <span>대표자 {company.representatives || "-"}</span>
          <span>사업자번호 {company.biz_no || "-"}</span>
          <span>보고일 {company.report_date || "-"}</span>
        </div>
      </section>

      {/* 주요 패널 그리드 */}
      <section className="detail-grid">
        <HealthPanel companyId={company.id} health={health} />
        <KeyMetricsPanel metrics={key_metrics} />
      </section>

      {/* 탭 기반 재무제표 */}
      <FinancialTabs tables={tables} companyId={company.id} />

      {/* 특이사항 노트 */}
      <NotesPanel notes={notes} />
    </DashboardShell>
  );
```

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/app/company/[companyId]/page.tsx
git commit -m "feat: redesign company detail page with corporate blue theme and financial tabs"
```

---

## Task 5: 동작 확인

- [ ] **Step 1: 개발 서버 실행**

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: 상세페이지 접속 확인**

브라우저에서 `/company/{임의의companyId}` 접속 후 아래를 확인한다.

1. 배경이 쿨 그레이(`#f1f5f9`)이고 glassmorphism 없음
2. 헤더 바에 회사명, 업종/주요제품 배지, 메타 정보 표시
3. 재무건전성 패널 grade-badge가 파란색
4. 재무제표 탭이 표시되고 탭 클릭 시 테이블 전환
5. 기간 필터(1년/3년/5년) 클릭 시 컬럼 수 변경
6. 엑셀 다운로드 버튼 표시

- [ ] **Step 3: 목록 페이지 확인**

`/` 접속 후 색상 테마가 함께 파란색 계열로 바뀌었는지 확인한다.
