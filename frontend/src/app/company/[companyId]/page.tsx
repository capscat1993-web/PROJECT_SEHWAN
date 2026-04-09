import { CompanyDetailPage } from "@/components/company-detail-page";
import { fetchInitialCompanyDetail } from "@/lib/server-api";
import type { CompanySummary, KeyMetricsResponse } from "@/lib/types";

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ companyId: string }>;
}) {
  const { companyId } = await params;
  const id = Number(companyId);

  let initialCompany: CompanySummary | undefined = undefined;
  let initialKeyMetrics: KeyMetricsResponse | undefined = undefined;
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
