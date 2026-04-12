import Link from "next/link";
import { notFound } from "next/navigation";

import { DashboardShell } from "@/components/dashboard-shell";
import { FinancialTabs } from "@/components/financial-tabs";
import { HealthPanel } from "@/components/health-panel";
import { KeyMetricsPanel } from "@/components/key-metrics-panel";
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
    grade_note?: string;
    data_note?: string;
    data_completeness_pct?: number;
    domains: {
      name: string;
      score: number;
      max_score: number;
      items: {
        label: string;
        score: number;
        max_score: number;
        configured_max_score?: number;
        value: number | null;
        unit: string;
        benchmark: string;
        item_grade: string;
        is_missing?: boolean;
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
  financial_statements: Record<
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

  const { company, health, key_metrics, financial_statements } = dashboard;

  return (
    <DashboardShell>
      <div className="detail-report">
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

      <section className="detail-grid">
        <KeyMetricsPanel metrics={key_metrics} />
      </section>

      <section className="detail-section">
        <FinancialTabs statements={financial_statements} companyId={company.id} />
      </section>

      <section className="detail-grid">
        <HealthPanel companyId={company.id} health={health} />
      </section>
      </div>
    </DashboardShell>
  );
}
