import Link from "next/link";
import { notFound } from "next/navigation";

import { DashboardShell } from "@/components/dashboard-shell";
import { HealthPanel } from "@/components/health-panel";
import { KeyMetricsPanel } from "@/components/key-metrics-panel";
import { NotesPanel } from "@/components/notes-panel";
import { SectionTable } from "@/components/section-table";
import { apiFetch } from "@/lib/api";

type DashboardPayload = {
  company: {
    id: number;
    company_name: string;
    representatives: string | null;
    biz_no: string | null;
    report_date: string | null;
    industry: string | null;
    main_product: string | null;
    imported_at: string | null;
  };
  health: {
    grade: string;
    total_score: number;
    recommendation: string;
    period: string;
    evaluation_opinion_lines: string[];
    domains: {
      name: string;
      score: number;
      max_score: number;
      items: {
        label: string;
        score: number;
        max_score: number;
        value: number | null;
        unit: string;
        benchmark: string;
        item_grade: string;
      }[];
    }[];
  };
  sections: string[];
  notes: { section: string; line: string }[];
  key_metrics: {
    periods: string[];
    unit: string;
    metrics: Record<string, Record<string, number | null>>;
  };
  tables: Record<
    string,
    {
      section: string;
      periods: string[];
      unit: string;
      rows: {
        metric: string;
        values: Record<string, { raw: string; num: number | null }>;
      }[];
    }
  >;
};

export default async function CompanyPage({ params }: { params: { companyId: string } }) {
  let dashboard: DashboardPayload;

  try {
    dashboard = await apiFetch<DashboardPayload>(`/api/companies/${params.companyId}/dashboard`);
  } catch {
    notFound();
  }

  const { company, health, key_metrics, notes, tables } = dashboard;

  return (
    <DashboardShell>
      <section className="detail-hero">
        <div>
          <Link href="/" className="back-link">
            전체 목록으로 돌아가기
          </Link>
          <span className="eyebrow">Company Radar</span>
          <h1>{company.company_name}</h1>
          <p className="detail-subtitle">
            {company.industry || "업종 미분류"} · {company.main_product || "주요 제품 정보 없음"}
          </p>
        </div>

        <div className="detail-meta-card">
          <div>
            <span>대표자</span>
            <strong>{company.representatives || "-"}</strong>
          </div>
          <div>
            <span>사업자번호</span>
            <strong>{company.biz_no || "-"}</strong>
          </div>
          <div>
            <span>보고일</span>
            <strong>{company.report_date || "-"}</strong>
          </div>
        </div>
      </section>

      <section className="detail-grid">
        <HealthPanel companyId={company.id} health={health} />
        <KeyMetricsPanel metrics={key_metrics} />
      </section>

      <section className="detail-grid detail-grid-secondary">
        <NotesPanel notes={notes} />
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Section Snapshot</span>
              <h2>재무 표</h2>
            </div>
            <p>핵심 섹션을 기간별 비교 테이블로 정리했습니다.</p>
          </div>
          <div className="stacked-sections">
            {Object.values(tables).map((table) => (
              <SectionTable key={table.section} table={table} />
            ))}
          </div>
        </div>
      </section>
    </DashboardShell>
  );
}
