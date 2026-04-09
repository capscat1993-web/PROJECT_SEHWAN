"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { apiFetchJson, getErrorMessage } from "@/lib/api";
import { formatDateLabel } from "@/lib/format";
import type { AsyncStatus, CompanySummary } from "@/lib/types";

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

      <div className="glass-card rounded-3xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-indigo-500 text-white">
                {["#", "기업명", "대표자", "업종", "주요제품", "사업자번호", "보고일"].map((h) => (
                  <th key={h} className="px-5 py-4 text-left text-xs font-bold uppercase tracking-wider">
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
                    <Link href={`/company/${company.id}`} className="font-bold text-indigo-600 hover:text-indigo-800 transition-colors">
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
                  <td className="px-5 py-4 text-sm text-slate-500 max-w-[200px] truncate">{company.main_product || "-"}</td>
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
