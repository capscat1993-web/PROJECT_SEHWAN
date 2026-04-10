export function SectionTable({
  table,
}: Readonly<{
  table: {
    section: string;
    periods: string[];
    unit: string;
    rows: {
      metric: string;
      values: Record<string, { raw: string; num: number | null }>;
    }[];
  };
}>) {
  return (
    <div className="section-card">
      <div className="section-card-header">
        <div>
          <h3>{table.section}</h3>
          <span>{table.unit ? `단위 ${table.unit}` : "단위 미기재"}</span>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>지표</th>
              {table.periods.map((period) => (
                <th key={period}>{period}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.slice(0, 18).map((row) => (
              <tr key={row.metric}>
                <td>{row.metric}</td>
                {table.periods.map((period) => (
                  <td key={period}>{row.values[period]?.raw || "-"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
