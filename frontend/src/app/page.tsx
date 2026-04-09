import { CompanyListPage } from "@/components/company-list-page";
import { fetchInitialCompanies } from "@/lib/server-api";
import type { CompanySummary } from "@/lib/types";

export default async function HomePage() {
  let initialCompanies: CompanySummary[] = [];
  try {
    initialCompanies = await fetchInitialCompanies();
  } catch {
    // 서버 사이드 프리패치 실패 시 클라이언트 폴백
  }
  return <CompanyListPage initialCompanies={initialCompanies} />;
}
