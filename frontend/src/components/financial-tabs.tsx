"use client";

import { useMemo, useState } from "react";

type StatementRow = {
  metric: string;
  values: Record<string, { raw: string; num: number | null }>;
};

type StatementData = {
  section: string;
  periods: string[];
  unit: string;
  rows: StatementRow[];
};

type StatementsMap = Record<string, StatementData>;

type DisplayEntry =
  | {
      type: "section";
      key: string;
      label: string;
      rows: StatementRow[];
      expanded: boolean;
      toggleKey: string;
    }
  | {
      type: "row";
      row: StatementRow;
      depth: number;
      tone: "default" | "summary" | "subtle";
    };

type RowTone = "default" | "summary" | "subtle";

const TAB_ORDER = ["income", "balance", "cashflow"] as const;

const CHART_CONFIG: Record<
  string,
  {
    metrics: string[];
    tone: string;
  }
> = {
  income: {
    metrics: ["매출액", "영업이익", "당기순이익"],
    tone: "financial-chart--income",
  },
  balance: {
    metrics: ["자산총계", "부채총계", "자본총계"],
    tone: "financial-chart--balance",
  },
  cashflow: {
    metrics: ["손익활동CF/총부채(%)", "손익활동CF/총자본(%)", "영업활동CF/차입금(%)"],
    tone: "financial-chart--cashflow",
  },
};

const BALANCE_SECTIONS = [
  {
    label: "자산 [개요]",
    toggleKey: "balance-assets",
    rows: ["유동자산", "당좌자산", "재고자산", "비유동자산", "자산총계"],
  },
  {
    label: "부채 [개요]",
    toggleKey: "balance-liabilities",
    rows: ["유동부채", "비유동부채", "부채총계"],
  },
  {
    label: "자본 [개요]",
    toggleKey: "balance-equity",
    rows: ["자본총계", "부채와자본총계"],
  },
] as const;

const INCOME_SECTIONS = [
  {
    label: "매출",
    toggleKey: "income-sales",
    rows: ["매출액", "매출원가", "매출총이익"],
  },
  {
    label: "영업손익",
    toggleKey: "income-operating",
    rows: ["판매비와관리비", "영업이익"],
  },
  {
    label: "최종손익",
    toggleKey: "income-bottom-line",
    rows: ["이자비용", "법인세차감전순손익", "계속사업이익(손실)", "당기순이익"],
  },
] as const;

function normalizeUnit(unit: string): string {
  if (unit.includes("백만원")) {
    return "백만원";
  }
  if (unit.includes("천원")) {
    return "천원";
  }
  if (unit.includes("억원")) {
    return "억원";
  }
  if (unit.includes("%")) {
    return "%";
  }
  return unit;
}

function toEok(value: number | null, unit: string): number | null {
  if (value === null) {
    return null;
  }
  if (unit.includes("억원")) {
    return value;
  }
  if (unit.includes("백만원")) {
    return value / 100;
  }
  if (unit.includes("천원")) {
    return value / 100_000;
  }
  if (unit.includes("원")) {
    return value / 100_000_000;
  }
  return value;
}

function formatChartValue(value: number | null, unit: string): string {
  if (value === null) {
    return "-";
  }

  if (normalizeUnit(unit) === "%") {
    return `${value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}%`;
  }

  const eok = toEok(value, unit);
  if (eok === null) {
    return "-";
  }

  return `${eok.toLocaleString("ko-KR", {
    maximumFractionDigits: eok >= 100 ? 0 : 1,
  })}억`;
}

function buildTicks(maxValue: number): number[] {
  const safeMax = Math.max(maxValue, 1);
  const magnitude = 10 ** Math.max(0, Math.floor(Math.log10(safeMax)));
  const step = Math.ceil(safeMax / 4 / magnitude) * magnitude;
  return [step * 4, step * 3, step * 2, step, 0];
}

function isSummaryMetric(statementKey: string, metric: string): boolean {
  if (statementKey === "balance") {
    return ["자산총계", "부채총계", "자본총계", "부채와자본총계"].includes(metric);
  }
  if (statementKey === "income") {
    return ["매출액", "매출총이익", "영업이익", "당기순이익"].includes(metric);
  }
  return false;
}

function buildDisplayEntries(
  statementKey: string,
  rows: StatementRow[],
  expanded: Record<string, boolean>,
): DisplayEntry[] {
  if (statementKey === "cashflow") {
    return rows.map((row) => ({
      type: "row",
      row,
      depth: 0,
      tone: "default",
    }));
  }

  const rowMap = new Map(rows.map((row) => [row.metric, row]));
  const sections = statementKey === "balance" ? BALANCE_SECTIONS : INCOME_SECTIONS;
  const entries: DisplayEntry[] = [];
  const used = new Set<string>();

  for (const section of sections) {
    const sectionRows = section.rows
      .map((metric) => rowMap.get(metric))
      .filter((row): row is StatementRow => Boolean(row));

    if (sectionRows.length === 0) {
      continue;
    }

    const sectionExpanded = expanded[section.toggleKey] ?? true;
    entries.push({
      type: "section",
      key: section.label,
      label: section.label,
      rows: sectionRows,
      expanded: sectionExpanded,
      toggleKey: section.toggleKey,
    });

    if (!sectionExpanded) {
      continue;
    }

    for (const row of sectionRows) {
      used.add(row.metric);
      let depth = 0;
      let tone: RowTone = "default";

      if (statementKey === "balance") {
        if (["당좌자산", "재고자산"].includes(row.metric)) {
          depth = 1;
          tone = "subtle";
        } else if (isSummaryMetric(statementKey, row.metric)) {
          tone = "summary";
        }
      } else if (statementKey === "income" && isSummaryMetric(statementKey, row.metric)) {
        tone = "summary";
      }

      entries.push({
        type: "row",
        row,
        depth,
        tone,
      });
    }
  }

  for (const row of rows) {
    if (!used.has(row.metric)) {
      entries.push({
        type: "row",
        row,
        depth: 0,
        tone: isSummaryMetric(statementKey, row.metric) ? "summary" : "default",
      });
    }
  }

  return entries;
}

function FinancialStatementChart({
  statementKey,
  table,
}: Readonly<{
  statementKey: string;
  table: StatementData;
}>) {
  const config = CHART_CONFIG[statementKey];
  const chartRows = table.rows.filter((row) => config.metrics.includes(row.metric));
  const normalizedUnit = normalizeUnit(table.unit);

  if (table.rows.length === 0 || chartRows.length === 0) {
    return <div className="financial-chart-empty">현금흐름분석 데이터가 없습니다.</div>;
  }

  const chartData = table.periods.map((period) => ({
    period,
    values: chartRows.map((row) => ({
      label: row.metric,
      raw: row.values[period]?.num ?? null,
      chartValue:
        normalizedUnit === "%"
          ? row.values[period]?.num ?? null
          : toEok(row.values[period]?.num ?? null, normalizedUnit),
    })),
  }));

  const maxValue = Math.max(
    ...chartData.flatMap((group) => group.values.map((item) => Math.abs(item.chartValue ?? 0))),
    1,
  );
  const ticks = buildTicks(maxValue * 1.08);

  const svgWidth = 940;
  const svgHeight = 290;
  const margin = { top: 28, right: 18, bottom: 42, left: 54 };
  const plotWidth = svgWidth - margin.left - margin.right;
  const plotHeight = svgHeight - margin.top - margin.bottom;
  const groupWidth = plotWidth / Math.max(chartData.length, 1);
  const barGroupWidth = Math.min(220, groupWidth * 0.72);
  const barWidth = barGroupWidth / Math.max(chartRows.length, 1);
  const unitLabel = normalizedUnit === "%" ? "%" : "억";

  const getY = (value: number) => margin.top + plotHeight - (value / (ticks[0] || 1)) * plotHeight;

  return (
    <div className={`financial-statement-chart ${config.tone}`}>
      <div className="financial-statement-legend">
        {chartRows.map((row, index) => (
          <span key={row.metric} className={`legend-item legend-item--${index + 1}`}>
            {row.metric}
          </span>
        ))}
      </div>

      <svg className="financial-chart-svg" viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="none">
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={margin.left}
              y1={getY(tick)}
              x2={svgWidth - margin.right}
              y2={getY(tick)}
              className={`financial-chart-line${tick === 0 ? " baseline" : ""}`}
            />
            <text x={margin.left - 10} y={getY(tick) + 4} className="financial-chart-tick" textAnchor="end">
              {tick === 0 ? "0" : `${tick.toLocaleString("ko-KR")}${unitLabel}`}
            </text>
          </g>
        ))}

        {chartData.map((group, groupIndex) => {
          const groupX = margin.left + groupWidth * groupIndex + (groupWidth - barGroupWidth) / 2;
          return (
            <g key={group.period}>
              {group.values.map((item, itemIndex) => {
                const value = item.chartValue ?? 0;
                const x = groupX + barWidth * itemIndex + 6;
                const y = getY(Math.max(value, 0));
                const height = Math.max(8, plotHeight - (y - margin.top));

                return (
                  <g key={`${group.period}-${item.label}`}>
                    <text
                      x={x + barWidth / 2 - 6}
                      y={Math.max(margin.top + 12, y - 8)}
                      className="financial-chart-value"
                      textAnchor="middle"
                    >
                      {formatChartValue(item.raw, normalizedUnit)}
                    </text>
                    <rect
                      x={x}
                      y={y}
                      width={Math.max(18, barWidth - 12)}
                      height={height}
                      rx={0}
                      className={`financial-chart-bar series-${itemIndex + 1}`}
                    />
                  </g>
                );
              })}

              <text
                x={groupX + barGroupWidth / 2}
                y={svgHeight - 12}
                className="financial-chart-period"
                textAnchor="middle"
              >
                {group.period}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function FinancialTabs({
  statements,
  companyId,
}: Readonly<{
  statements: StatementsMap;
  companyId: number;
}>) {
  const availableTabs = useMemo(() => TAB_ORDER.filter((key) => statements[key]), [statements]);
  const [activeTab, setActiveTab] = useState(availableTabs[0] ?? "");
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    "balance-assets": true,
    "balance-liabilities": true,
    "balance-equity": true,
    "income-sales": true,
    "income-operating": true,
    "income-bottom-line": true,
  });

  if (availableTabs.length === 0) {
    return <div className="empty-card">표시할 재무제표 데이터가 없습니다.</div>;
  }

  const activeTable = statements[activeTab];
  const exportUrl = `/api/companies/${companyId}/health/export`;
  const displayEntries = buildDisplayEntries(activeTab, activeTable.rows, expandedSections);

  const toggleSection = (toggleKey: string) => {
    setExpandedSections((current) => ({
      ...current,
      [toggleKey]: !(current[toggleKey] ?? true),
    }));
  };

  return (
    <div className="financial-tabs-wrap report-panel financial-statements-panel">
      <div className="panel-header financial-panel-heading">
        <div>
          <span className="eyebrow">Financial Statements</span>
          <h2>재무정보</h2>
        </div>
        <a href={exportUrl} className="ghost-button">
          엑셀 저장
        </a>
      </div>

      <div className="financial-tabs-header">
        <div className="financial-tab-list">
          {availableTabs.map((tab) => (
            <button
              key={tab}
              className={`financial-tab-btn${activeTab === tab ? " active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {statements[tab].section}
            </button>
          ))}
        </div>
      </div>

      <div className="financial-tab-body">
        <FinancialStatementChart statementKey={activeTab} table={activeTable} />

        <div className="table-wrap financial-statement-table">
          <div className="financial-table-meta">
            <p className="financial-table-unit">단위: {normalizeUnit(activeTable.unit) || "-"}</p>
            <p className="financial-table-hint">요약 행은 강조색으로 표시됩니다.</p>
          </div>

          <table>
            <thead>
              <tr>
                <th>구분</th>
                {activeTable.periods.map((period, index) => (
                  <th key={period} className={index === activeTable.periods.length - 1 ? "is-latest" : ""}>
                    {period}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activeTable.rows.length > 0 ? (
                displayEntries.map((entry, index) =>
                  entry.type === "section" ? (
                    <tr key={`${entry.key}-${index}`} className="financial-section-row">
                      <td className="financial-section-title">
                        <button
                          type="button"
                          className={`financial-section-toggle${entry.expanded ? " expanded" : ""}`}
                          onClick={() => toggleSection(entry.toggleKey)}
                          aria-label={entry.expanded ? `${entry.label} 접기` : `${entry.label} 펼치기`}
                          aria-expanded={entry.expanded}
                        >
                          <span />
                        </button>
                        <span>{entry.label}</span>
                      </td>
                      {activeTable.periods.map((period) => (
                        <td key={period}>-</td>
                      ))}
                    </tr>
                  ) : (
                    <tr
                      key={entry.row.metric}
                      className={`financial-data-row${entry.tone === "summary" ? " is-summary" : ""}${
                        entry.tone === "subtle" ? " is-subtle" : ""
                      }`}
                    >
                      <td className="financial-metric-cell">
                        <div className="financial-metric-inner" style={{ paddingLeft: `${entry.depth * 18}px` }}>
                          <span className="financial-row-bullet" />
                          <span>{entry.row.metric}</span>
                        </div>
                      </td>
                      {activeTable.periods.map((period, periodIndex) => (
                        <td key={period} className={periodIndex === activeTable.periods.length - 1 ? "is-latest" : ""}>
                          {entry.row.values[period]?.raw || "-"}
                        </td>
                      ))}
                    </tr>
                  ),
                )
              ) : (
                <tr>
                  <td>데이터 없음</td>
                  {activeTable.periods.map((period) => (
                    <td key={period}>-</td>
                  ))}
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
