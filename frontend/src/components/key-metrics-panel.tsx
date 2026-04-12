"use client";

type MetricSeries = Record<string, number | null>;

type ChartTone = {
  accentClass: string;
};

const CHART_TONES: Record<string, ChartTone> = {
  매출액: { accentClass: "metric-chart-card--sales" },
  영업이익: { accentClass: "metric-chart-card--operating" },
  당기순이익: { accentClass: "metric-chart-card--net" },
};

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

function formatEok(value: number | null): string {
  if (value === null) {
    return "-";
  }

  return `${value.toLocaleString("ko-KR", {
    maximumFractionDigits: value >= 100 ? 0 : 1,
  })}억원`;
}

function formatShortEok(value: number | null): string {
  return formatEok(value).replace("억원", "억");
}

function formatDelta(value: number | null): string {
  if (value === null) {
    return "-";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function formatPeriod(period: string): string {
  return period.replace(".", "/");
}

function buildTicks(maxAbs: number, hasNegative: boolean): number[] {
  const roughStep = maxAbs / (hasNegative ? 2 : 3);
  const stepBase = Math.max(1, roughStep);
  const magnitude = 10 ** Math.max(0, Math.floor(Math.log10(stepBase)));
  const roundedStep = Math.ceil(stepBase / magnitude) * magnitude;
  const roundedMax = roundedStep * (hasNegative ? 2 : 3);

  if (!hasNegative) {
    return [roundedMax, roundedMax * (2 / 3), roundedMax / 3, 0];
  }

  return [roundedMax, roundedMax / 2, 0, -(roundedMax / 2), -roundedMax];
}

function getBarPathY(value: number, domainMin: number, domainMax: number, plotHeight: number): number {
  const ratio = (value - domainMin) / (domainMax - domainMin || 1);
  return plotHeight - ratio * plotHeight;
}

function expandDomain(min: number, max: number, hasNegative: boolean) {
  const positiveHeadroom = max === 0 ? 1 : Math.abs(max) * 0.08;

  if (!hasNegative) {
    return {
      domainMin: 0,
      domainMax: max + positiveHeadroom,
    };
  }

  const negativeHeadroom = min === 0 ? 1 : Math.abs(min) * 0.08;
  return {
    domainMin: min - negativeHeadroom,
    domainMax: max + positiveHeadroom,
  };
}

function MetricChartCard({
  label,
  periods,
  series,
  sourceUnit,
}: Readonly<{
  label: string;
  periods: string[];
  series: MetricSeries;
  sourceUnit: string;
}>) {
  const tone = CHART_TONES[label] ?? CHART_TONES.매출액;
  const chartData = periods.map((period) => ({
    period,
    value: toEok(series[period] ?? null, sourceUnit),
  }));

  const currentEntry = chartData.at(-1);
  const previousEntry = chartData.at(-2);
  const current = currentEntry?.value ?? null;
  const previous = previousEntry?.value ?? null;
  const delta =
    current !== null && previous !== null && previous !== 0
      ? ((current - previous) / Math.abs(previous)) * 100
      : null;

  const maxAbs = Math.max(...chartData.map(({ value }) => Math.abs(value ?? 0)), 1);
  const hasNegative = chartData.some(({ value }) => (value ?? 0) < 0);
  const ticks = buildTicks(maxAbs, hasNegative);
  const expandedDomain = expandDomain(hasNegative ? ticks.at(-1) ?? -maxAbs : 0, ticks[0] ?? maxAbs, hasNegative);
  const domainMin = expandedDomain.domainMin;
  const domainMax = expandedDomain.domainMax;

  const svgWidth = 320;
  const svgHeight = 280;
  const margin = { top: 18, right: 12, bottom: 42, left: 62 };
  const plotWidth = svgWidth - margin.left - margin.right;
  const plotHeight = svgHeight - margin.top - margin.bottom;
  const zeroY = margin.top + getBarPathY(0, domainMin, domainMax, plotHeight);
  const step = plotWidth / Math.max(chartData.length, 1);
  const barWidth = Math.min(56, step * 0.68);

  return (
    <article className={`metric-chart-card ${tone.accentClass}`}>
      <div className="metric-chart-head">
        <div>
          <h3>{label}</h3>
          <span>{currentEntry?.period ?? "-"} 기준</span>
        </div>
      </div>

      <div className="metric-chart-summary">
        <div>
          <span>
            {currentEntry?.period ?? "-"} {label}
          </span>
          <strong>{formatEok(current)}</strong>
        </div>
        <div>
          <span>{previousEntry?.period ?? "-"} 대비</span>
          <strong className={delta !== null && delta < 0 ? "down" : "up"}>{formatDelta(delta)}</strong>
        </div>
      </div>

      <div className="metric-chart-body">
        <svg
          className="metric-chart-svg"
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          role="img"
          aria-label={`${label} 최근 ${chartData.length}개 연도 추이`}
          preserveAspectRatio="none"
        >
          {ticks.map((tick) => {
            const y = margin.top + getBarPathY(tick, domainMin, domainMax, plotHeight);
            return (
              <g key={tick}>
                <line
                  x1={margin.left}
                  y1={y}
                  x2={svgWidth - margin.right}
                  y2={y}
                  className={tick === 0 ? "metric-chart-line metric-chart-line--baseline" : "metric-chart-line"}
                />
                <text x={margin.left - 10} y={y + 4} className="metric-chart-tick" textAnchor="end">
                  {tick === 0 ? "0" : `${tick.toLocaleString("ko-KR")}억`}
                </text>
              </g>
            );
          })}

          {chartData.map(({ period, value }, index) => {
            const safeValue = value ?? 0;
            const x = margin.left + step * index + (step - barWidth) / 2;
            const valueY = margin.top + getBarPathY(safeValue, domainMin, domainMax, plotHeight);
            const barTop = safeValue >= 0 ? valueY : zeroY;
            const barHeight = Math.max(Math.abs(zeroY - valueY), value === null ? 0 : 8);
            const labelY = safeValue >= 0 ? Math.max(margin.top + 12, barTop - 8) : Math.min(svgHeight - margin.bottom - 8, barTop + barHeight + 16);

            return (
              <g key={period}>
                <text x={x + barWidth / 2} y={labelY} className="metric-chart-value" textAnchor="middle">
                  {formatShortEok(value)}
                </text>
                <rect
                  x={x}
                  y={barTop}
                  width={barWidth}
                  height={barHeight}
                  rx={0}
                  className={`metric-chart-bar${safeValue < 0 ? " negative" : ""}`}
                />
                <text
                  x={x + barWidth / 2}
                  y={svgHeight - margin.bottom + 20}
                  className="metric-chart-period"
                  textAnchor="middle"
                >
                  {formatPeriod(period)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </article>
  );
}

export function KeyMetricsPanel({
  metrics,
}: Readonly<{
  metrics: {
    periods: string[];
    unit: string;
    metrics: Record<string, MetricSeries>;
  };
}>) {
  const items = Object.entries(metrics.metrics);

  return (
    <div className="panel report-panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Performance Stream</span>
          <h2>핵심 실적 지표</h2>
        </div>
        <p>단위 억원</p>
      </div>

      <div className="metric-chart-list">
        {items.map(([label, series]) => (
          <MetricChartCard
            key={label}
            label={label}
            periods={metrics.periods}
            series={series}
            sourceUnit={metrics.unit}
          />
        ))}
      </div>
    </div>
  );
}
