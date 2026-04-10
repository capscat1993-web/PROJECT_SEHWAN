export function KeyMetricsPanel({
  metrics,
}: Readonly<{
  metrics: {
    periods: string[];
    unit: string;
    metrics: Record<string, Record<string, number | null>>;
  };
}>) {
  const items = Object.entries(metrics.metrics);
  const allValues = items.flatMap(([, series]) => Object.values(series).filter((value): value is number => value !== null));
  const max = Math.max(...allValues.map((value) => Math.abs(value)), 1);

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Performance Stream</span>
          <h2>핵심 실적 지표</h2>
        </div>
        <p>{metrics.unit ? `단위 ${metrics.unit}` : "단위 정보 없음"}</p>
      </div>

      <div className="metric-series-list">
        {items.map(([label, series]) => (
          <div key={label} className="series-card">
            <strong>{label}</strong>
            <div className="series-bars">
              {metrics.periods.map((period) => {
                const value = series[period];
                const width = value === null ? 8 : `${(Math.abs(value) / max) * 100}%`;
                return (
                  <div key={period} className="series-row">
                    <span>{period}</span>
                    <div className="series-track">
                      <div className={`series-fill ${value !== null && value < 0 ? "negative" : ""}`} style={{ width }} />
                    </div>
                    <strong>{value === null ? "-" : value.toLocaleString()}</strong>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
