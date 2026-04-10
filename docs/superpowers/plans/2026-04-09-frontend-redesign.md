# Frontend Redesign — StockQuest Style Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Next.js 프론트엔드 두 페이지(기업 목록, 기업 상세)를 StockQuest 스타일(인디고 컬러, 글래스 카드, bento 그리드, 고정 사이드바, 플로팅 AI 챗)로 전면 재작성한다.

**Architecture:** Tailwind CSS v3 도입 + Google Fonts(Bungee, Noto Sans KR) 적용. 기존 iframe 라우트를 실제 Next.js 컴포넌트로 교체. 사이드바는 layout.tsx에서 전역 렌더링.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS v3, Google Fonts

---

## File Map

| 파일 | 액션 | 역할 |
|---|---|---|
| `frontend/package.json` | 수정 | tailwindcss, postcss, autoprefixer 추가 |
| `frontend/postcss.config.mjs` | 신규 | PostCSS 플러그인 설정 |
| `frontend/tailwind.config.ts` | 신규 | Tailwind 테마 토큰 정의 |
| `frontend/src/app/globals.css` | 전면 교체 | Tailwind 디렉티브 + glass-card/bento-card 유틸리티 |
| `frontend/src/app/layout.tsx` | 수정 | Google Fonts 주입, Sidebar 포함 |
| `frontend/src/app/page.tsx` | 수정 | iframe → CompanyListPage 서버 컴포넌트 |
| `frontend/src/app/company/[companyId]/page.tsx` | 수정 | iframe → CompanyDetailPage 서버 컴포넌트 |
| `frontend/src/components/sidebar.tsx` | 신규 | 고정 좌측 사이드바 |
| `frontend/src/components/chat-panel.tsx` | 전면 교체 | 플로팅 위젯 (toggle 버튼 + 슬라이드업 패널) |
| `frontend/src/components/company-list-page.tsx` | 전면 교체 | 목록 페이지 리디자인 |
| `frontend/src/components/company-detail-page.tsx` | 전면 교체 | 상세 페이지 리디자인 |

---

## Task 1: Tailwind CSS 설치 및 기본 설정

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Modify: `frontend/src/app/globals.css`

- [ ] **Step 1: Tailwind 패키지 설치**

```bash
cd frontend && npm install -D tailwindcss postcss autoprefixer
```

Expected: `node_modules/tailwindcss` 생성됨

- [ ] **Step 2: postcss.config.mjs 생성**

```js
// frontend/postcss.config.mjs
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
export default config;
```

- [ ] **Step 3: tailwind.config.ts 생성**

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        secondary: "#f43f5e",
        accent: "#facc15",
        "brand-bg": "#f0f2ff",
      },
      fontFamily: {
        headline: ["Bungee", "cursive"],
        body: ["Noto Sans KR", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 4: globals.css 전면 교체**

```css
/* frontend/src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html,
  body {
    @apply m-0 p-0 w-full min-h-screen bg-brand-bg text-slate-900;
    font-family: "Noto Sans KR", sans-serif;
  }
  * {
    box-sizing: border-box;
  }
}

@layer components {
  .glass-card {
    @apply bg-white/80 backdrop-blur-md border-4 border-white shadow-xl;
  }
  .bento-card {
    @apply rounded-3xl p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl;
  }
  .font-headline {
    font-family: "Bungee", cursive;
  }
}
```

- [ ] **Step 5: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공 (타입 에러 없음)

- [ ] **Step 6: 커밋**

```bash
cd frontend && git add package.json package-lock.json postcss.config.mjs tailwind.config.ts src/app/globals.css
git commit -m "feat: install Tailwind CSS v3 and configure design tokens"
```

---

## Task 2: layout.tsx — 폰트 주입 + Sidebar 포함

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Create: `frontend/src/components/sidebar.tsx`

- [ ] **Step 1: sidebar.tsx 생성**

```tsx
// frontend/src/components/sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function HomeIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M5 9.2h3V19H5V9.2zM10.6 5h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z" />
    </svg>
  );
}

function LogoIcon() {
  return (
    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
    </svg>
  );
}

function NavItem({
  href,
  active,
  label,
  children,
}: {
  href: string;
  active: boolean;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`group relative flex items-center justify-center w-12 h-12 rounded-2xl transition-all ${
        active
          ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/30"
          : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
      }`}
    >
      {children}
      <span className="absolute left-14 bg-slate-900 text-white text-[10px] px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        {label}
      </span>
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const isHome = pathname === "/";
  const isDetail = pathname.startsWith("/company");

  return (
    <aside className="fixed left-4 top-4 bottom-4 w-20 bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl z-50 flex flex-col items-center py-8 border-4 border-white">
      <div className="w-12 h-12 bg-indigo-500 rounded-2xl flex items-center justify-center mb-10 shadow-lg shadow-indigo-500/30">
        <LogoIcon />
      </div>
      <nav className="flex flex-col gap-6">
        <NavItem href="/" active={isHome} label="기업 목록">
          <HomeIcon />
        </NavItem>
        <NavItem href="/" active={isDetail} label="재무 분석">
          <ChartIcon />
        </NavItem>
      </nav>
    </aside>
  );
}
```

- [ ] **Step 2: layout.tsx 수정 — 폰트 + Sidebar**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "기업 재무 리포트",
  description: "국내 기업의 재무 건전성 분석 플랫폼",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Bungee&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Sidebar />
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 3: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공

- [ ] **Step 4: 커밋**

```bash
cd frontend && git add src/app/layout.tsx src/components/sidebar.tsx
git commit -m "feat: add global sidebar and Google Fonts (Bungee + Noto Sans KR)"
```

---

## Task 3: 라우트 교체 — iframe → Next.js 컴포넌트

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/company/[companyId]/page.tsx`

- [ ] **Step 1: page.tsx 수정**

```tsx
// frontend/src/app/page.tsx
import { CompanyListPage } from "@/components/company-list-page";
import { fetchInitialCompanies } from "@/lib/server-api";

export default async function HomePage() {
  let initialCompanies = [];
  try {
    initialCompanies = await fetchInitialCompanies();
  } catch {
    // 서버 사이드 프리패치 실패 시 클라이언트 폴백
  }
  return <CompanyListPage initialCompanies={initialCompanies} />;
}
```

- [ ] **Step 2: company/[companyId]/page.tsx 수정**

```tsx
// frontend/src/app/company/[companyId]/page.tsx
import { CompanyDetailPage } from "@/components/company-detail-page";
import { fetchInitialCompanyDetail } from "@/lib/server-api";

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ companyId: string }>;
}) {
  const { companyId } = await params;
  const id = Number(companyId);

  let initialCompany = undefined;
  let initialKeyMetrics = undefined;
  let initialSections: string[] = [];

  try {
    const data = await fetchInitialCompanyDetail(id);
    initialCompany = data.company;
    initialKeyMetrics = data.keyMetrics;
    initialSections = data.sections;
  } catch {
    // 서버 사이드 프리패치 실패 시 클라이언트 폴백
  }

  return (
    <CompanyDetailPage
      companyId={id}
      initialCompany={initialCompany}
      initialKeyMetrics={initialKeyMetrics}
      initialSections={initialSections}
    />
  );
}
```

- [ ] **Step 3: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공

- [ ] **Step 4: 커밋**

```bash
cd frontend && git add src/app/page.tsx src/app/company/
git commit -m "feat: replace iframe routes with Next.js component routes"
```

---

## Task 4: ChatPanel — 플로팅 위젯으로 재작성

**Files:**
- Modify: `frontend/src/components/chat-panel.tsx`

- [ ] **Step 1: chat-panel.tsx 전면 교체**

```tsx
// frontend/src/components/chat-panel.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetchJson, getErrorMessage } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

interface Message {
  id: string;
  role: "assistant" | "user" | "error";
  content: string;
}

interface ChatPanelProps {
  title: string;
  subtitle: string;
  companyId?: number;
  companyName?: string;
}

function createIntroMessage(companyName?: string) {
  return companyName
    ? `${companyName}의 재무 흐름, 업황, 리스크 요인을 자연어로 물어보세요.`
    : "최신 업황, 업계 뉴스, 거래 판단 포인트를 바로 질문할 수 있습니다.";
}

function BotIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.66 0-3 1.34-3 3s1.34 3 3 3v4c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-4c1.66 0 3-1.34 3-3s-1.34-3-3-3zm-2 10H6V7h12v12zM9 11c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1zm6 0c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1zm-3 6c1.9 0 3.63-.99 4.58-2.6H7.42C8.37 16.01 10.1 17 12 17z" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

export function ChatPanel({ title, subtitle, companyId, companyName }: ChatPanelProps) {
  const [open, setOpen] = useState(false);
  const initialMessage = useMemo(() => createIntroMessage(companyName), [companyName]);
  const [messages, setMessages] = useState<Message[]>([
    { id: "intro", role: "assistant", content: initialMessage },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMessages([{ id: "intro", role: "assistant", content: createIntroMessage(companyName) }]);
  }, [companyId, companyName]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [messages, sending]);

  async function handleSubmit() {
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    setMessages((curr) => [...curr, { id: `user-${Date.now()}`, role: "user", content: trimmed }]);
    setInput("");
    setSending(true);

    try {
      const payload = await apiFetchJson<ChatResponse>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ company_id: companyId, message: trimmed }),
      });
      setMessages((curr) => [
        ...curr,
        { id: `assistant-${Date.now()}`, role: payload.error ? "error" : "assistant", content: payload.reply },
      ]);
    } catch (error) {
      setMessages((curr) => [
        ...curr,
        { id: `error-${Date.now()}`, role: "error", content: getErrorMessage(error) },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed bottom-8 right-8 z-[100]">
      <div className="flex flex-col items-end gap-4">
        {open && (
          <div className="w-96 glass-card rounded-3xl overflow-hidden flex flex-col shadow-2xl border-indigo-200/50 animate-fade-in">
            {/* 헤더 */}
            <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-inner text-indigo-500">
                  <BotIcon />
                </div>
                <div>
                  <p className="text-white font-bold text-sm leading-none">{title}</p>
                  <p className="text-white/60 text-[10px] font-bold uppercase tracking-tighter mt-0.5">
                    Online · Ready to Help
                  </p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-white/40 hover:text-white transition-colors"
              >
                <CloseIcon />
              </button>
            </div>

            {/* 메시지 영역 */}
            <div className="h-72 p-5 overflow-y-auto space-y-3 bg-slate-50/50" ref={scrollRef}>
              <p className="text-[10px] text-slate-400 text-center mb-4">{subtitle}</p>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-3xl text-xs leading-relaxed ${
                      msg.role === "user"
                        ? "bg-indigo-500 text-white rounded-br-none"
                        : msg.role === "error"
                          ? "bg-rose-50 text-rose-700 border border-rose-200 rounded-tl-none"
                          : "bg-white border-2 border-slate-100 shadow-sm text-slate-700 rounded-tl-none"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white border-2 border-slate-100 shadow-sm rounded-3xl rounded-tl-none px-4 py-3 flex items-center gap-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 입력 영역 */}
            <div className="p-4 bg-white border-t border-slate-100">
              <div className="relative">
                <input
                  type="text"
                  className="w-full pl-5 pr-12 py-3 bg-slate-50 border-none rounded-full text-xs font-medium focus:outline-none focus:ring-4 focus:ring-indigo-500/10 placeholder:text-slate-400"
                  placeholder="질문을 입력하세요..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleSubmit();
                    }
                  }}
                />
                <button
                  onClick={() => void handleSubmit()}
                  disabled={sending}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full flex items-center justify-center shadow-lg shadow-indigo-500/20 transition-all hover:scale-105 disabled:opacity-50"
                >
                  <SendIcon />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 토글 버튼 */}
        <button
          onClick={() => setOpen((v) => !v)}
          className="w-16 h-16 bg-indigo-500 rounded-full shadow-2xl shadow-indigo-500/30 flex items-center justify-center border-4 border-white hover:scale-110 transition-all"
        >
          <ChatIcon />
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공

- [ ] **Step 3: 커밋**

```bash
cd frontend && git add src/components/chat-panel.tsx
git commit -m "feat: rewrite ChatPanel as floating toggle widget"
```

---

## Task 5: company-list-page.tsx 리디자인

**Files:**
- Modify: `frontend/src/components/company-list-page.tsx`

- [ ] **Step 1: company-list-page.tsx 전면 교체**

```tsx
// frontend/src/components/company-list-page.tsx
"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { apiFetchJson, getErrorMessage } from "@/lib/api";
import { formatDateLabel } from "@/lib/format";
import type { AsyncStatus, CompanySummary } from "@/lib/types";

// ── 아이콘 ───────────────────────────────────────────────────────────────────

function BuildingIcon() {
  return (
    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z" />
    </svg>
  );
}

function GridIcon() {
  return (
    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z" />
    </svg>
  );
}

function DatabaseIcon() {
  return (
    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 3C7.58 3 4 4.79 4 7v10c0 2.21 3.58 4 8 4s8-1.79 8-4V7c0-2.21-3.58-4-8-4zm6 14c0 .5-2.13 2-6 2s-6-1.5-6-2v-1.72C7.27 16.3 9.5 17 12 17s4.73-.7 6-1.72V17zm0-4c0 .5-2.13 2-6 2s-6-1.5-6-2v-1.72C7.27 12.3 9.5 13 12 13s4.73-.7 6-1.72V13zm-6-2c-3.87 0-6-1.5-6-2s2.13-2 6-2 6 1.5 6 2-2.13 2-6 2z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    </svg>
  );
}

// ── StatCard ────────────────────────────────────────────────────────────────

type StatColor = "indigo" | "rose" | "emerald" | "amber";

const COLOR_MAP: Record<StatColor, { ring: string; bg: string; icon: string; value: string }> = {
  indigo:  { ring: "border-indigo-50",  bg: "bg-indigo-100",  icon: "text-indigo-600",  value: "text-indigo-500" },
  rose:    { ring: "border-rose-50",    bg: "bg-rose-100",    icon: "text-rose-600",    value: "text-rose-500" },
  emerald: { ring: "border-emerald-50", bg: "bg-emerald-100", icon: "text-emerald-600", value: "text-emerald-500" },
  amber:   { ring: "border-amber-50",   bg: "bg-amber-100",   icon: "text-amber-600",   value: "text-amber-500" },
};

function StatCard({
  icon,
  label,
  value,
  color,
  small = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: StatColor;
  small?: boolean;
}) {
  const c = COLOR_MAP[color];
  return (
    <div className="glass-card p-5 rounded-3xl flex flex-col items-center gap-2 min-w-[120px]">
      <div className={`w-12 h-12 rounded-full ${c.bg} flex items-center justify-center ${c.icon} border-4 ${c.ring}`}>
        {icon}
      </div>
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{label}</p>
      {small ? (
        <p className="text-xs font-bold text-slate-700 text-center">{value}</p>
      ) : (
        <p className={`text-2xl font-headline ${c.value}`}>{value}</p>
      )}
    </div>
  );
}

// ── Main ────────────────────────────────────────────────────────────────────

export function CompanyListPage({ initialCompanies = [] }: { initialCompanies?: CompanySummary[] }) {
  const [companies, setCompanies] = useState<CompanySummary[]>(initialCompanies);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<AsyncStatus>(initialCompanies.length ? "success" : "idle");
  const [errorMessage, setErrorMessage] = useState("");
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    let ignore = false;
    async function loadCompanies() {
      setStatus("loading");
      setErrorMessage("");
      try {
        const data = await apiFetchJson<CompanySummary[]>(
          `/api/companies?q=${encodeURIComponent(deferredQuery.trim())}`,
        );
        if (!ignore) {
          setCompanies(data);
          setStatus("success");
        }
      } catch (error) {
        if (!ignore) {
          setStatus("error");
          setErrorMessage(getErrorMessage(error));
        }
      }
    }
    void loadCompanies();
    return () => {
      ignore = true;
    };
  }, [deferredQuery]);

  const industryCount = new Set(companies.map((c) => c.industry).filter(Boolean)).size;
  const latestReport = companies.map((c) => c.report_date).filter(Boolean).sort().at(-1);

  return (
    <main className="pl-28 pr-10 pt-10 pb-20 min-h-screen">
      {/* ── 헤더 ── */}
      <header className="flex flex-col lg:flex-row justify-between items-start mb-12 gap-8">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <span className="bg-amber-400 text-slate-900 font-bold px-4 py-1.5 rounded-full text-xs uppercase tracking-wider shadow-sm border-b-4 border-amber-500">
              NICE D&amp;B
            </span>
            <span className="bg-white/50 px-4 py-1.5 rounded-full text-xs font-bold text-slate-500">
              재무 분석 플랫폼
            </span>
          </div>
          <h1 className="font-headline text-5xl lg:text-6xl text-slate-900 leading-none mb-3">
            기업 재무{" "}
            <span className="text-indigo-500 block lg:inline">리포트</span>
          </h1>
          <p className="text-xl text-slate-500 font-medium">국내 기업의 재무 건전성을 한눈에 파악하세요.</p>
        </div>

        <div className="flex flex-wrap gap-4 justify-end">
          <StatCard icon={<BuildingIcon />} label="등록 기업" value={String(companies.length)} color="indigo" />
          <StatCard icon={<GridIcon />} label="업종 수" value={String(industryCount)} color="rose" />
          <StatCard icon={<CalendarIcon />} label="최근 보고일" value={formatDateLabel(latestReport)} color="emerald" small />
          <StatCard icon={<DatabaseIcon />} label="데이터 출처" value="NICE D&B" color="amber" small />
        </div>
      </header>

      {/* ── 검색 ── */}
      <div className="glass-card rounded-3xl p-5 mb-8 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-lg">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
            <SearchIcon />
          </span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="기업명 검색..."
            className="w-full pl-12 pr-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:outline-none focus:ring-4 focus:ring-indigo-500/10 placeholder:text-slate-400"
          />
        </div>
        <p className="text-sm text-slate-500 shrink-0">
          총 <strong className="text-indigo-600">{companies.length}</strong>개 기업
        </p>
      </div>

      {status === "error" && (
        <div className="bg-rose-50 border-2 border-rose-200 text-rose-700 rounded-2xl p-4 mb-6 text-sm">
          {errorMessage}
        </div>
      )}

      {/* ── 테이블 ── */}
      <div className="glass-card rounded-3xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-indigo-500 text-white">
                {["#", "기업명", "대표자", "업종", "주요제품", "사업자번호", "보고일"].map((h) => (
                  <th
                    key={h}
                    className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {companies.map((company, index) => (
                <tr key={company.id} className="hover:bg-indigo-50/50 transition-colors">
                  <td className="px-5 py-4 text-xs text-slate-400 font-mono">{index + 1}</td>
                  <td className="px-5 py-4">
                    <Link
                      href={`/company/${company.id}`}
                      className="font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
                    >
                      {company.company_name}
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">{company.representatives || "-"}</td>
                  <td className="px-5 py-4">
                    {company.industry ? (
                      <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-bold rounded-full">
                        {company.industry}
                      </span>
                    ) : (
                      <span className="text-slate-400 text-sm">-</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-500 max-w-[200px] truncate">
                    {company.main_product || "-"}
                  </td>
                  <td className="px-5 py-4 text-xs font-mono text-slate-500">{company.biz_no || "-"}</td>
                  <td className="px-5 py-4 text-sm text-slate-500">{formatDateLabel(company.report_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {status === "loading" && (
          <div className="p-12 text-center text-slate-400 text-sm">기업 목록을 불러오는 중입니다...</div>
        )}
        {status === "success" && companies.length === 0 && (
          <div className="p-12 text-center text-slate-400 text-sm">검색 결과가 없습니다.</div>
        )}
      </div>

      <ChatPanel title="AI 재무 분석" subtitle="재무 건전성, 최신 뉴스, 업계 동향 등을 질문해주세요." />
    </main>
  );
}
```

- [ ] **Step 2: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공

- [ ] **Step 3: 커밋**

```bash
cd frontend && git add src/components/company-list-page.tsx
git commit -m "feat: redesign company list page with StockQuest style"
```

---

## Task 6: company-detail-page.tsx 리디자인

**Files:**
- Modify: `frontend/src/components/company-detail-page.tsx`

- [ ] **Step 1: company-detail-page.tsx 전면 교체**

```tsx
// frontend/src/components/company-detail-page.tsx
"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { FinancialBarChart } from "@/components/financial-bar-chart";
import { HealthRadarChart } from "@/components/health-radar-chart";
import { apiFetchJson, getErrorMessage, getPublicApiBaseUrl } from "@/lib/api";
import {
  formatDateLabel,
  formatDelta,
  formatFinancialValue,
  formatHealthValue,
  formatNumber,
} from "@/lib/format";
import type {
  AsyncStatus,
  CompanySummary,
  FinancialTableResponse,
  HealthResponse,
  IncomeChartResponse,
  KeyMetricsResponse,
} from "@/lib/types";

type DetailTab = "overview" | "financial" | "health";

const PREFERRED_SECTIONS = ["손익계산서", "재무상태표", "자본변동표", "현금흐름분석", "현금흐름지표"];

const ITEM_GRADE_CLASS: Record<string, string> = {
  "A (양호)": "text-emerald-600 font-bold",
  "B (보통)": "text-amber-600 font-bold",
  "C (주의)": "text-orange-500 font-bold",
  "D (위험)": "text-rose-600 font-bold",
  "N/A": "text-slate-400",
};

const GRADE_BG: Record<string, string> = {
  "AAA": "bg-emerald-500",
  "AA+": "bg-emerald-500",
  "AA":  "bg-emerald-400",
  "AA-": "bg-emerald-400",
  "A+":  "bg-teal-500",
  "A":   "bg-teal-500",
  "A-":  "bg-teal-400",
  "BBB": "bg-amber-500",
  "BB":  "bg-orange-500",
  "B":   "bg-rose-500",
  "CCC": "bg-rose-600",
  "D":   "bg-slate-500",
};

function pickDefaultSection(sections: string[]) {
  return PREFERRED_SECTIONS.find((s) => sections.includes(s)) || sections[0] || "";
}

// ── 아이콘 ───────────────────────────────────────────────────────────────────

function ArrowUpIcon() {
  return (
    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
      <path d="M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z" />
    </svg>
  );
}

function ArrowDownIcon() {
  return (
    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
      <path d="M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z" />
    </svg>
  );
}

function TrendingIcon() {
  return (
    <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
      <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
    </svg>
  );
}

function FinanceIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z" />
    </svg>
  );
}

function HealthIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
    </svg>
  );
}

// ── Main ────────────────────────────────────────────────────────────────────

export function CompanyDetailPage({
  companyId,
  initialCompany,
  initialKeyMetrics,
  initialSections,
}: {
  companyId: number;
  initialCompany?: CompanySummary | null;
  initialKeyMetrics?: KeyMetricsResponse | null;
  initialSections?: string[];
}) {
  const [company, setCompany] = useState<CompanySummary | null>(initialCompany ?? null);
  const [keyMetrics, setKeyMetrics] = useState<KeyMetricsResponse | null>(initialKeyMetrics ?? null);
  const [sections, setSections] = useState<string[]>(initialSections ?? []);
  const [selectedSection, setSelectedSection] = useState(pickDefaultSection(initialSections ?? []));
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const [pageStatus, setPageStatus] = useState<AsyncStatus>(
    initialCompany && initialKeyMetrics ? "success" : "loading",
  );
  const [pageError, setPageError] = useState("");
  const [financialStatus, setFinancialStatus] = useState<AsyncStatus>("idle");
  const [healthStatus, setHealthStatus] = useState<AsyncStatus>("idle");
  const [incomeChart, setIncomeChart] = useState<IncomeChartResponse | null>(null);
  const [financialTables, setFinancialTables] = useState<Record<string, FinancialTableResponse>>({});
  const [health, setHealth] = useState<HealthResponse | null>(null);

  // ── 데이터 로드 ──

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      if (!Number.isFinite(companyId) || companyId <= 0) {
        setPageStatus("error");
        setPageError("유효한 기업 ID가 아닙니다.");
        return;
      }
      setPageStatus("loading");
      setPageError("");
      try {
        const [companyData, keyMetricsData, sectionData] = await Promise.all([
          apiFetchJson<CompanySummary>(`/api/companies/${companyId}`),
          apiFetchJson<KeyMetricsResponse>(`/api/companies/${companyId}/key_metrics`),
          apiFetchJson<string[]>(`/api/companies/${companyId}/sections`),
        ]);
        if (!ignore) {
          setCompany(companyData);
          setKeyMetrics(keyMetricsData);
          setSections(sectionData);
          setSelectedSection(pickDefaultSection(sectionData));
          setPageStatus("success");
        }
      } catch (error) {
        if (!ignore) {
          setPageStatus("error");
          setPageError(getErrorMessage(error));
        }
      }
    }
    void loadInitial();
    return () => { ignore = true; };
  }, [companyId]);

  useEffect(() => {
    let ignore = false;
    async function loadFinancial() {
      if (activeTab !== "financial" || !company) return;
      const currentSection = selectedSection || pickDefaultSection(sections);
      if (!currentSection) return;
      setFinancialStatus("loading");
      try {
        const chartPromise = incomeChart
          ? Promise.resolve(incomeChart)
          : apiFetchJson<IncomeChartResponse>(`/api/companies/${companyId}/income_chart`);
        const tablePromise = financialTables[currentSection]
          ? Promise.resolve(financialTables[currentSection])
          : apiFetchJson<FinancialTableResponse>(
              `/api/companies/${companyId}/financial_table?section=${encodeURIComponent(currentSection)}`,
            );
        const [chartData, tableData] = await Promise.all([chartPromise, tablePromise]);
        if (!ignore) {
          setIncomeChart(chartData);
          setFinancialTables((curr) => ({ ...curr, [currentSection]: tableData }));
          setFinancialStatus("success");
        }
      } catch (error) {
        if (!ignore) {
          setFinancialStatus("error");
          setPageError(getErrorMessage(error));
        }
      }
    }
    void loadFinancial();
    return () => { ignore = true; };
  }, [activeTab, company, companyId, financialTables, incomeChart, sections, selectedSection]);

  useEffect(() => {
    let ignore = false;
    async function loadHealth() {
      if (activeTab !== "health" || !company || health) return;
      setHealthStatus("loading");
      try {
        const healthData = await apiFetchJson<HealthResponse>(`/api/companies/${companyId}/health`);
        if (!ignore) { setHealth(healthData); setHealthStatus("success"); }
      } catch (error) {
        if (!ignore) { setHealthStatus("error"); setPageError(getErrorMessage(error)); }
      }
    }
    void loadHealth();
    return () => { ignore = true; };
  }, [activeTab, company, companyId, health]);

  // ── 핵심 지표 메모 ──

  const metricCards = useMemo(() => {
    if (!keyMetrics) return [];
    return Object.entries(keyMetrics.metrics).map(([label, values]) => {
      const periods = keyMetrics.periods.filter((p) => values[p] !== null && values[p] !== undefined);
      const latestPeriod = periods.at(-1);
      const previousPeriod = periods.length > 1 ? periods.at(-2) : null;
      const latestValue = latestPeriod ? values[latestPeriod] : null;
      const previousValue = previousPeriod ? values[previousPeriod] : null;
      return {
        label,
        latestPeriod,
        latestValue,
        previousPeriod,
        change: formatDelta(previousValue, latestValue),
      };
    });
  }, [keyMetrics]);

  // ── 로딩 / 에러 ──

  if (pageStatus === "loading") {
    return (
      <main className="pl-28 pr-10 pt-10 pb-20 min-h-screen flex items-center justify-center">
        <div className="glass-card rounded-3xl p-12 text-slate-400 text-sm">
          기업 상세 정보를 불러오는 중입니다...
        </div>
      </main>
    );
  }

  if (pageStatus === "error" || !company) {
    return (
      <main className="pl-28 pr-10 pt-10 pb-20 min-h-screen">
        <div className="bg-rose-50 border-2 border-rose-200 text-rose-700 rounded-2xl p-4 text-sm">{pageError}</div>
      </main>
    );
  }

  const currentTable = selectedSection ? financialTables[selectedSection] : null;

  return (
    <main className="pl-28 pr-10 pt-10 pb-20 min-h-screen">
      {/* ── 뒤로가기 ── */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-indigo-600 font-bold mb-8 transition-colors"
      >
        <BackIcon /> 목록으로
      </Link>

      {/* ── 히어로 헤더 ── */}
      <header className="flex flex-col lg:flex-row justify-between items-start mb-12 gap-8">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            {company.industry && (
              <span className="bg-amber-400 text-slate-900 font-bold px-4 py-1.5 rounded-full text-xs uppercase tracking-wider shadow-sm border-b-4 border-amber-500">
                {company.industry}
              </span>
            )}
            <span className="bg-white/50 px-4 py-1.5 rounded-full text-xs font-bold text-slate-500">
              보고일: {formatDateLabel(company.report_date)}
            </span>
          </div>
          <h1 className="font-headline text-5xl lg:text-6xl text-slate-900 leading-none mb-3">
            {company.company_name}
          </h1>
          <p className="text-lg text-slate-500 font-medium">
            {[
              company.representatives && `대표: ${company.representatives}`,
              company.biz_no && `사업자번호: ${company.biz_no}`,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>

        <div className="flex flex-wrap gap-4">
          {health && (
            <div className="glass-card p-6 rounded-3xl flex flex-col items-center gap-2 min-w-[140px]">
              <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 border-4 border-emerald-50">
                <ShieldIcon />
              </div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">재무건전성</p>
              <p className="text-2xl font-headline text-emerald-500">{health.grade}</p>
            </div>
          )}
          <div className="glass-card p-6 rounded-3xl flex flex-col items-center gap-2 min-w-[140px]">
            <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 border-4 border-indigo-50">
              <CalendarIcon />
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">보고일</p>
            <p className="text-sm font-bold text-slate-700 text-center">{formatDateLabel(company.report_date)}</p>
          </div>
        </div>
      </header>

      {/* ── 핵심 지표 ── */}
      {metricCards.length > 0 && (
        <section className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-10">
          {metricCards.map((metric) => (
            <article
              key={metric.label}
              className="glass-card rounded-3xl p-6 relative overflow-hidden group hover:scale-[1.02] transition-all"
            >
              <div className="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-opacity text-indigo-500">
                <TrendingIcon />
              </div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-2">
                {metric.label}
              </p>
              <p className="text-xl font-headline text-indigo-500 mb-2">
                {formatFinancialValue(metric.latestValue, keyMetrics?.unit || "")}
              </p>
              <div className="flex items-center gap-1 text-xs font-bold">
                {metric.change ? (
                  metric.change.value >= 0 ? (
                    <span className="text-emerald-500 flex items-center gap-1">
                      <ArrowUpIcon /> {metric.change.label}
                    </span>
                  ) : (
                    <span className="text-rose-500 flex items-center gap-1">
                      <ArrowDownIcon /> {metric.change.label}
                    </span>
                  )
                ) : (
                  <span className="text-slate-400">비교 없음</span>
                )}
              </div>
              <p className="text-[10px] text-slate-400 mt-1">{metric.latestPeriod || "-"}</p>
            </article>
          ))}
        </section>
      )}

      {/* ── 탭 ── */}
      <div className="flex gap-4 mb-10 overflow-x-auto pb-2">
        {(
          [
            { id: "overview" as const, label: "기업 개요", icon: <InfoIcon /> },
            { id: "financial" as const, label: "재무제표", icon: <FinanceIcon /> },
            { id: "health" as const, label: "재무건전성", icon: <HealthIcon /> },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            type="button"
            className={`px-8 py-3 rounded-2xl font-bold flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-indigo-500 text-white shadow-xl shadow-indigo-500/30"
                : "bg-white text-slate-600 hover:bg-slate-50 border-2 border-slate-100"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {pageError && activeTab !== "overview" && (
        <div className="bg-rose-50 border-2 border-rose-200 text-rose-700 rounded-2xl p-4 mb-6 text-sm">
          {pageError}
        </div>
      )}

      {/* ── 개요 탭 ── */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <article className="bento-card glass-card">
            <h2 className="font-headline text-lg text-slate-800 mb-6 flex items-center gap-2">
              <span className="p-2 bg-indigo-100 rounded-xl text-indigo-600">
                <InfoIcon />
              </span>
              기업 기본 정보
            </h2>
            <dl className="space-y-3">
              {[
                { label: "회사명", value: company.company_name },
                { label: "대표자", value: company.representatives },
                { label: "사업자번호", value: company.biz_no },
                { label: "보고일", value: formatDateLabel(company.report_date) },
                { label: "업종", value: company.industry },
                { label: "주요제품", value: company.main_product },
              ].map(({ label, value }) => (
                <div key={label} className="flex gap-3 bg-slate-50 rounded-2xl px-4 py-3">
                  <dt className="text-xs font-bold text-slate-400 uppercase tracking-tighter w-24 shrink-0 mt-0.5">
                    {label}
                  </dt>
                  <dd className="text-sm font-medium text-slate-700">{value || "-"}</dd>
                </div>
              ))}
            </dl>
          </article>

          <article className="bento-card glass-card">
            <h2 className="font-headline text-lg text-slate-800 mb-6 flex items-center gap-2">
              <span className="p-2 bg-amber-100 rounded-xl text-amber-600">
                <FinanceIcon />
              </span>
              보유 재무 섹션
            </h2>
            <div className="flex flex-wrap gap-2">
              {sections.map((section) => (
                <span
                  key={section}
                  className="px-4 py-2 bg-indigo-100 text-indigo-700 text-xs font-bold rounded-full"
                >
                  {section}
                </span>
              ))}
            </div>
          </article>
        </div>
      )}

      {/* ── 재무 탭 ── */}
      {activeTab === "financial" && (
        <div className="space-y-8">
          <article className="bento-card glass-card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-headline text-lg text-slate-800">손익 추이</h2>
              {incomeChart?.unit && (
                <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                  단위: {incomeChart.unit}
                </span>
              )}
            </div>
            {financialStatus === "loading" && !incomeChart ? (
              <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
                재무 차트를 불러오는 중입니다...
              </div>
            ) : (
              <FinancialBarChart
                periods={incomeChart?.periods ?? []}
                rows={incomeChart?.rows ?? []}
                unit={incomeChart?.unit ?? ""}
              />
            )}
          </article>

          <article className="bento-card glass-card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-headline text-lg text-slate-800">재무제표</h2>
              {currentTable?.unit && (
                <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
                  단위: {currentTable.unit}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mb-6">
              {sections.map((section) => (
                <button
                  key={section}
                  onClick={() => setSelectedSection(section)}
                  type="button"
                  className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
                    selectedSection === section
                      ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {section}
                </button>
              ))}
            </div>

            {financialStatus === "loading" && !currentTable ? (
              <div className="h-32 flex items-center justify-center text-slate-400 text-sm">
                재무표를 불러오는 중입니다...
              </div>
            ) : currentTable ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-indigo-500 text-white">
                      <th className="px-4 py-3 text-left text-xs font-bold uppercase">구분</th>
                      {currentTable.periods.map((p) => (
                        <th key={p} className="px-4 py-3 text-right text-xs font-bold uppercase">{p}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {currentTable.rows.map((row) => (
                      <tr key={row.metric} className="hover:bg-indigo-50/30 transition-colors">
                        <td className="px-4 py-3 text-sm text-slate-700 font-medium">{row.metric}</td>
                        {currentTable.periods.map((p) => (
                          <td key={`${row.metric}-${p}`} className="px-4 py-3 text-sm text-right text-slate-600 font-mono">
                            {row.values[p]?.raw || "-"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-slate-400 text-sm">데이터가 없습니다.</div>
            )}
          </article>
        </div>
      )}

      {/* ── 건전성 탭 ── */}
      {activeTab === "health" && (
        <div className="space-y-8">
          {healthStatus === "loading" && !health ? (
            <div className="glass-card rounded-3xl p-12 text-center text-slate-400 text-sm">
              재무건전성 분석을 불러오는 중입니다...
            </div>
          ) : health?.error ? (
            <div className="bg-rose-50 border-2 border-rose-200 text-rose-700 rounded-2xl p-4 text-sm">
              {health.error}
            </div>
          ) : health ? (
            <>
              {/* 점수 카드 */}
              <article className="bg-slate-900 text-white rounded-3xl p-8 flex flex-col md:flex-row gap-8 items-start">
                <div className="flex flex-col items-center shrink-0">
                  <div
                    className={`w-24 h-24 rounded-3xl flex items-center justify-center text-3xl font-headline text-white shadow-xl ${GRADE_BG[health.grade] || "bg-indigo-500"}`}
                  >
                    {health.grade}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-3 uppercase tracking-widest">재무건전성 등급</p>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-2">{health.recommendation}</h3>
                  <p className="text-slate-400 text-sm mb-4">
                    {health.period} 기준 · 총점 {health.total_score}점 · 데이터 완성도 {health.data_completeness_pct}%
                  </p>
                  <div className="space-y-2">
                    {[health.grade_note, health.data_note].filter(Boolean).map((note) => (
                      <div key={note} className="bg-slate-800 rounded-2xl p-3 text-sm text-slate-300">
                        {note}
                      </div>
                    ))}
                  </div>
                </div>
                <a
                  href={getPublicApiBaseUrl(`/api/export-health/${companyId}`)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-6 py-3 bg-indigo-500 hover:bg-indigo-400 text-white rounded-2xl font-bold text-sm transition-colors flex items-center gap-2 shrink-0"
                >
                  <DownloadIcon /> Excel 다운로드
                </a>
              </article>

              {/* 차트 + 바 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <article className="bento-card glass-card">
                  <h2 className="font-headline text-lg text-slate-800 mb-6">영역별 건전성</h2>
                  <HealthRadarChart domains={health.domains} />
                </article>

                <article className="bento-card glass-card">
                  <h2 className="font-headline text-lg text-slate-800 mb-6">영역별 점수</h2>
                  <div className="space-y-5">
                    {health.domains.map((domain) => {
                      const percent =
                        domain.max_score > 0 ? Math.round((domain.score / domain.max_score) * 100) : 0;
                      return (
                        <div key={domain.name}>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-bold text-slate-700">{domain.name}</span>
                            <strong className="text-sm text-indigo-600 font-headline">
                              {domain.score} / {domain.max_score}
                            </strong>
                          </div>
                          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-indigo-500 to-indigo-400 h-full rounded-full transition-all"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </article>
              </div>

              {/* 세부 지표 테이블 */}
              <article className="bento-card glass-card">
                <h2 className="font-headline text-lg text-slate-800 mb-6">세부 지표</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-indigo-500 text-white">
                        {["영역", "지표", "값", "벤치마크", "점수", "등급"].map((h) => (
                          <th key={h} className="px-4 py-3 text-left text-xs font-bold uppercase">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {health.domains.flatMap((domain) =>
                        domain.items.map((item) => (
                          <tr
                            key={`${domain.name}-${item.label}`}
                            className="hover:bg-indigo-50/30 transition-colors"
                          >
                            <td className="px-4 py-3 text-xs text-slate-500">{domain.name}</td>
                            <td className="px-4 py-3 text-sm font-medium text-slate-700">{item.label}</td>
                            <td className="px-4 py-3 text-sm font-mono text-slate-600">
                              {formatHealthValue(item.value, item.unit)}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-500">{item.benchmark}</td>
                            <td className="px-4 py-3 text-sm font-mono text-indigo-600">
                              {item.max_score > 0
                                ? `${formatNumber(item.score)} / ${formatNumber(item.max_score)}`
                                : "평가 제외"}
                            </td>
                            <td className={`px-4 py-3 text-sm ${ITEM_GRADE_CLASS[item.item_grade] || ""}`}>
                              {item.item_grade}
                            </td>
                          </tr>
                        )),
                      )}
                    </tbody>
                  </table>
                </div>
              </article>

              {/* 평가 의견 */}
              <article className="bento-card glass-card">
                <h2 className="font-headline text-lg text-slate-800 mb-6">평가 의견</h2>
                <div className="space-y-3">
                  {health.evaluation_opinion_lines.map((line) => (
                    <div key={line} className="bg-indigo-50 border-l-4 border-indigo-400 rounded-r-2xl px-5 py-3 text-sm text-slate-700">
                      {line}
                    </div>
                  ))}
                </div>
              </article>
            </>
          ) : (
            <div className="glass-card rounded-3xl p-12 text-center text-slate-400 text-sm">
              건전성 데이터가 없습니다.
            </div>
          )}
        </div>
      )}

      <ChatPanel
        title="AI 재무 분석"
        subtitle="이 기업의 재무 데이터와 업황을 기반으로 답변합니다."
        companyId={companyId}
        companyName={company.company_name}
      />
    </main>
  );
}
```

- [ ] **Step 2: 빌드 확인**

```bash
cd frontend && npm run build
```

Expected: 빌드 성공

- [ ] **Step 3: 커밋**

```bash
cd frontend && git add src/components/company-detail-page.tsx
git commit -m "feat: redesign company detail page with StockQuest style"
```

---

## 완료 기준

- `npm run build` 성공
- 기업 목록 페이지: 고정 사이드바, 헤더 + 4개 통계 카드, 검색바, 인디고 테이블
- 기업 상세 페이지: 히어로 헤더, 핵심 지표 bento 카드, 탭 3개, 각 탭 컨텐츠 정상 렌더링
- AI 챗: 우하단 플로팅 위젯, 토글 버튼 동작
