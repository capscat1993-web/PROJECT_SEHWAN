export function MetricCard({
  label,
  value,
  accent,
}: Readonly<{
  label: string;
  value: string;
  accent: "sunrise" | "ocean" | "mint";
}>) {
  return (
    <div className={`metric-card metric-${accent}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
