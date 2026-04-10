import Link from "next/link";

import { DashboardShell } from "@/components/dashboard-shell";
import { IndustryPanel } from "@/components/industry-panel";
import { MetricCard } from "@/components/metric-card";
import { SearchBar } from "@/components/search-bar";
import { apiFetch, Company, Overview } from "@/lib/api";

type HomeProps = {
  searchParams?: {
    q?: string;
  };
};

export default async function Home({ searchParams }: HomeProps) {
  const query = searchParams?.q?.trim() || "";
  const [overview, companies] = await Promise.all([
    apiFetch<Overview>("/api/overview"),
    apiFetch<Company[]>(`/api/companies${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  ]);

  const featured = companies.slice(0, 12);

  return (
    <DashboardShell>
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">Auto Finance Atlas</span>
          <h1>자동차 부품사 재무 데이터를 더 선명하게 읽는 운영 대시보드</h1>
          <p>
            Django 백엔드가 SQLite 재무 데이터를 정리하고, Next.js 프론트가 회사별 건전성 등급과 핵심
            지표를 입체적으로 보여줍니다.
          </p>
          <SearchBar initialQuery={query} />
        </div>

        <div className="hero-highlight">
          <div className="spotlight-card">
            <span>최근 기준일</span>
            <strong>{overview.latest_report_date || "데이터 없음"}</strong>
            <p>최신 적재 보고일 기준으로 전체 회사를 탐색할 수 있습니다.</p>
          </div>
          <div className="spotlight-grid">
            {overview.latest_companies.slice(0, 3).map((company) => (
              <Link key={company.id} href={`/company/${company.id}`} className="mini-company-card">
                <strong>{company.company_name}</strong>
                <span>{company.industry || "업종 미상"}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="등록 기업 수" value={overview.total_companies.toLocaleString()} accent="sunrise" />
        <MetricCard label="재무 데이터 행 수" value={overview.total_value_rows.toLocaleString()} accent="ocean" />
        <MetricCard label="검색 결과" value={featured.length.toLocaleString()} accent="mint" />
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Company Index</span>
              <h2>회사 목록</h2>
            </div>
            <p>{query ? `"${query}" 검색 결과` : "업종, 제품, 회사명을 기준으로 탐색하세요."}</p>
          </div>

          <div className="company-grid">
            {featured.map((company) => (
              <Link key={company.id} href={`/company/${company.id}`} className="company-card">
                <div className="company-card-top">
                  <span className="tag">{company.industry || "업종 미분류"}</span>
                  <span className="subtle">{company.report_date || "보고일 미상"}</span>
                </div>
                <h3>{company.company_name}</h3>
                <p>{company.main_product || "주요 제품 정보 없음"}</p>
                <dl className="card-meta">
                  <div>
                    <dt>대표자</dt>
                    <dd>{company.representatives || "-"}</dd>
                  </div>
                  <div>
                    <dt>사업자번호</dt>
                    <dd>{company.biz_no || "-"}</dd>
                  </div>
                </dl>
              </Link>
            ))}
            {!featured.length && <div className="empty-card">검색 결과가 없습니다. 다른 키워드로 다시 찾아보세요.</div>}
          </div>
        </div>

        <IndustryPanel industries={overview.top_industries} />
      </section>
    </DashboardShell>
  );
}
