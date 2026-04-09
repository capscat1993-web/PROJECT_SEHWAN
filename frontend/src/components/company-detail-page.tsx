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
                <span key={section} className="px-4 py-2 bg-indigo-100 text-indigo-700 text-xs font-bold rounded-full">
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
