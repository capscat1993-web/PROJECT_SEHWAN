# Frontend Redesign — StockQuest Style

**Date:** 2026-04-09  
**Status:** Approved

## Goal

Next.js 프론트엔드(기업 재무 분석 플랫폼)의 두 페이지를 레퍼런스 디자인(StockQuest gamified dashboard) 스타일로 재작성한다. 기능과 데이터는 그대로 유지하고, 비주얼만 교체한다.

## Stack Changes

- **Tailwind CSS v4** 설치 (PostCSS 방식)
- **Google Fonts**: Bungee (헤드라인·숫자 강조), Noto Sans KR (한국어 본문)
- 기존 `globals.css` 레거시 클래스 전면 교체

## Design Tokens

| Token | Value |
|---|---|
| Primary | `#6366f1` (indigo-500) |
| Secondary | `#f43f5e` (rose-500) |
| Accent | `#facc15` (amber-400) |
| Brand BG | `#f0f2ff` |
| Surface | `#ffffff` |
| Dark surface | `#0f172a` |

## Architecture

### 공통 레이아웃
- `layout.tsx`: Google Fonts 주입, `<body>` 배경 색 적용
- `Sidebar` 컴포넌트 (신규): 고정 왼쪽 사이드바 w-20, 아이콘 네비게이션
- 모든 페이지: `pl-28` padding-left로 사이드바 공간 확보

### Glass Card 패턴
```
bg-white/80 backdrop-blur-md border-4 border-white shadow-xl rounded-3xl
```

### Bento Card 패턴
```
rounded-3xl p-6 transition-all hover:scale-[1.02] hover:shadow-2xl border-4 border-transparent hover:border-white
```

## Pages

### 1. 기업 목록 페이지 (`company-list-page.tsx`)

**헤더**
- "기업 재무 리포트" 타이틀 (Bungee, 4xl)
- 등록기업·업종·보고일·출처 — glass-card 4개 가로 배열

**검색바**
- rounded-full input, 그림자, 기업 수 표시

**테이블**
- 인디고 계열 헤더, hover row 강조
- 업종: pill badge (indigo/10 bg)
- 기업명: 클릭 링크 강조 (primary color)

**AI 챗**
- 우하단 고정 플로팅 위젯으로 래핑

### 2. 기업 상세 페이지 (`company-detail-page.tsx`)

**히어로 헤더**
- 회사명 크게 (Bungee), 업종 badge, 보고일
- 재무건전성 등급 glass-card, 대표자 glass-card

**핵심 지표 그리드**
- glass-card 4열, 수치 Bungee 강조, 증감 arrow 색상

**탭**
- pill 버튼 3개, active: primary bg + white text

**개요 탭**
- 2열 bento: 기본정보 dl + 재무섹션 태그 클라우드

**재무 탭**
- 차트 card + 섹션 chip row + 테이블 card

**건전성 탭**
- 점수 배지 + 등급 카드 (dark surface)
- 레이더 차트 card + 도메인 progress bar card
- 상세 지표 테이블

**AI 챗**
- 우하단 플로팅 위젯 (ChatPanel 래핑, 토글 버튼 포함)

## File Changes

| File | Action |
|---|---|
| `frontend/package.json` | tailwindcss, @tailwindcss/postcss 추가 |
| `frontend/postcss.config.mjs` | 신규 생성 |
| `frontend/tailwind.config.ts` | 신규 생성 (토큰 설정) |
| `frontend/src/app/globals.css` | 전면 교체 |
| `frontend/src/app/layout.tsx` | Google Fonts 주입 |
| `frontend/src/components/sidebar.tsx` | 신규 생성 |
| `frontend/src/components/company-list-page.tsx` | 전면 재작성 |
| `frontend/src/components/company-detail-page.tsx` | 전면 재작성 |
| `frontend/src/components/chat-panel.tsx` | 플로팅 위젯으로 재작성 |
