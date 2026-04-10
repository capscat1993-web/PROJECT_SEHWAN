"use client";

import { useState } from "react";

type TableData = {
  section: string;
  periods: string[];
  unit: string;
  rows: {
    metric: string;
    values: Record<string, { raw: string; num: number | null }>;
  }[];
};

export function FinancialTabs({
  tables,
  companyId,
}: Readonly<{
  tables: Record<string, TableData>;
  companyId: number;
}>) {
  const sections = Object.keys(tables);
  const [activeTab, setActiveTab] = useState(sections[0] ?? "");
  const [periodYears, setPeriodYears] = useState<1 | 3 | 5>(5);

  if (sections.length === 0) {
    return <div className="empty-card">재무 데이터가 없습니다.</div>;
  }

  const table = tables[activeTab];

  const filteredPeriods = [...table.periods]
    .sort((a, b) => b.localeCompare(a))
    .slice(0, periodYears)
    .sort((a, b) => a.localeCompare(b));

  const exportUrl = `/api/companies/${companyId}/health/export`;

  return (
    <div className="financial-tabs-wrap">
      <div className="financial-tabs-header">
        <div className="financial-tab-list">
          {sections.map((section) => (
            <button
              key={section}
              className={`financial-tab-btn${activeTab === section ? " active" : ""}`}
              onClick={() => setActiveTab(section)}
            >
              {section}
            </button>
          ))}
        </div>

        <div className="financial-tab-controls">
          {([1, 3, 5] as const).map((y) => (
            <button
              key={y}
              className={`period-btn${periodYears === y ? " active" : ""}`}
              onClick={() => setPeriodYears(y)}
            >
              {y}년
            </button>
          ))}
          <a
            href={exportUrl}
            className="ghost-button"
            style={{ fontSize: "0.82rem", padding: "6px 14px" }}
          >
            엑셀↓
          </a>
        </div>
      </div>

      <div className="financial-tab-body">
        <div className="table-wrap">
          {table.unit && (
            <p style={{ margin: "12px 16px 4px", fontSize: "0.82rem", color: "var(--muted)" }}>
              단위: {table.unit}
            </p>
          )}
          <table>
            <thead>
              <tr>
                <th>지표</th>
                {filteredPeriods.map((period) => (
                  <th key={period}>{period}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row) => (
                <tr key={row.metric}>
                  <td>{row.metric}</td>
                  {filteredPeriods.map((period) => (
                    <td key={period}>{row.values[period]?.raw || "-"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
