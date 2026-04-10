export function IndustryPanel({
  industries,
}: Readonly<{
  industries: { name: string; count: number }[];
}>) {
  const max = Math.max(...industries.map((industry) => industry.count), 1);

  return (
    <aside className="panel accent-panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Industry Mix</span>
          <h2>상위 업종 분포</h2>
        </div>
      </div>
      <div className="industry-list">
        {industries.map((industry) => (
          <div key={industry.name} className="industry-row">
            <div>
              <strong>{industry.name}</strong>
              <span>{industry.count}개사</span>
            </div>
            <div className="industry-bar">
              <div style={{ width: `${(industry.count / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
