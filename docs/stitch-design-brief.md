# Google Stitch Design Brief

## Project Overview

This project is a web dashboard for reviewing Korean company financial data.

The product helps users:

- search and browse companies
- review core company information
- inspect financial statement trends
- check a financial health score and risk summary
- ask follow-up questions through an AI chat assistant

The current UI feels too plain and utilitarian. I want a cleaner, more modern, more premium dashboard experience with stronger visual hierarchy and better usability.

## Product Context

- Backend: FastAPI
- Frontend: Next.js App Router
- Primary users: internal business users, finance reviewers, sales/partnership teams, managers
- Data type: company profile, financial statements, financial health evaluation, AI-generated analysis
- Locale: Korean-first interface

## Core Pages To Design

### 1. Company List Page

Main purpose:

- show all companies in the database
- allow search by company name
- provide quick summary stats
- let users move into a specific company detail page

Current functional elements:

- top summary cards
- search input
- company table
- floating AI chat widget

Needed improvement:

- make the page feel like a real decision-support dashboard, not a basic admin table
- improve table readability and scanability
- make search and filtering feel more prominent
- give summary cards more visual importance

### 2. Company Detail Page

Main purpose:

- show a single company overview
- present key metrics at a glance
- let users switch between Overview / Financial / Health tabs

Current functional elements:

- company header
- key metric cards
- tabs for overview, financial statements, and financial health
- floating AI chat widget

Needed improvement:

- stronger page structure and hierarchy
- better use of whitespace and section grouping
- clearer navigation between tabs
- more polished executive-dashboard feeling

### 3. Financial Tab

Main purpose:

- show revenue/income trend chart
- show financial statement tables by section

Current functional elements:

- bar chart for trends
- section chips/buttons
- financial data table

Needed improvement:

- charts should feel more polished and presentation-ready
- tables should look dense but not overwhelming
- section switching should be intuitive and clearly active

### 4. Financial Health Tab

Main purpose:

- show company health grade
- explain recommendation / risk level
- visualize domain scores
- list detailed indicator scores
- allow Excel export

Current functional elements:

- grade badge
- recommendation summary
- radar chart
- progress bars by domain
- detailed health indicator table
- note cards / analysis comments
- Excel export button

Needed improvement:

- this should feel like the signature screen of the product
- make the grade and recommendation visually impactful
- create a strong sense of trust and analytical depth
- support fast scanning for both executives and analysts

### 5. AI Chat Panel

Main purpose:

- let users ask about a company or general financial/risk questions

Current functional elements:

- message list
- textarea
- send button

Needed improvement:

- more refined assistant panel styling
- should feel integrated with the dashboard, not like an afterthought
- keep it compact, useful, and visually calm

## Design Goals

- modern financial analytics dashboard
- premium but not flashy
- high trust, high clarity, high readability
- works well for data-heavy screens
- feels useful for real business work

## Desired Visual Direction

Please avoid generic startup dashboard styling.

I want something with:

- clean and confident layout
- strong typography hierarchy
- refined card system
- balanced use of color
- subtle depth, not flat and boring
- serious business tone with modern polish

Possible direction:

- background: warm light neutral or slightly tinted off-white
- primary accents: deep navy, slate, muted teal, or restrained emerald
- status colors: clear but elegant
- charts: professional and low-noise

Please avoid:

- childish SaaS visuals
- overly playful colors
- purple-heavy palette
- excessive gradients
- overly dark cyber style
- crowded enterprise legacy look

## UX Requirements

- desktop-first, but responsive on laptop and tablet widths
- excellent readability for tables and charts
- easy scanning of key business signals
- clear visual distinction between summary, detail, and action areas
- important actions should stand out without overwhelming the page
- support Korean text gracefully

## Information Architecture Guidance

Please preserve these major content groups:

- company summary
- key metrics
- financial chart and tables
- financial health score and explanation
- AI chat assistant

Suggested emphasis:

- make the Health tab the most impressive and differentiated part of the product
- make the List page feel like an intelligent portfolio overview
- make the Detail page feel like an executive briefing plus analyst workspace

## Deliverables Requested

Please propose:

1. overall visual direction
2. layout structure for the company list page
3. layout structure for the company detail page
4. treatment for charts, tables, metric cards, tabs, and chat panel
5. responsive behavior
6. color palette, typography, spacing, and component style guidance

If possible, generate a high-fidelity dashboard-style design that can later be implemented in Next.js.

## Important Notes

- The interface is for Korean company financial analysis.
- The product should look credible enough for internal business decision-making.
- Visual polish matters, but clarity matters more.
- I care more about strong structure and taste than decorative effects.
