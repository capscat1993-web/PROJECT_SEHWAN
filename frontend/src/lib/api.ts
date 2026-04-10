const publicBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const serverBaseUrl = process.env.API_BASE_URL || publicBaseUrl;

export type Company = {
  id: number;
  company_name: string;
  representatives: string | null;
  biz_no: string | null;
  report_date: string | null;
  industry: string | null;
  main_product: string | null;
  imported_at: string | null;
};

export type Overview = {
  total_companies: number;
  latest_report_date: string | null;
  total_value_rows: number;
  top_industries: { name: string; count: number }[];
  latest_companies: Pick<Company, "id" | "company_name" | "industry" | "main_product" | "report_date">[];
};

export async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${serverBaseUrl}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export function getClientApiBaseUrl(): string {
  return publicBaseUrl;
}
