"use client";

import { getClientApiBaseUrl } from "@/lib/api";

export function HealthPanel({
  companyId,
  health,
}: Readonly<{
  companyId: number;
  health: {
    grade: string;
    total_score: number;
    recommendation: string;
    period: string;
    evaluation_opinion_lines: string[];
    domains: {
      name: string;
      score: number;
      max_score: number;
      items: {
        label: string;
        score: number;
        max_score: number;
        value: number | null;
        unit: string;
        benchmark: string;
        item_grade: string;
      }[];
    }[];
  };
}>) {
  const exportUrl = `${getClientApiBaseUrl()}/api/companies/${companyId}/health/export`;

  return (
    <div className="panel health-panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Health Score</span>
          <h2>재무건전성 평가</h2>
        </div>
        <a href={exportUrl} className="ghost-button">
          엑셀 다운로드
        </a>
      </div>

      <div className="health-topline">
        <div className="grade-badge">{health.grade}</div>
        <div>
          <strong>{health.total_score}점</strong>
          <p>{health.recommendation}</p>
          <span>기준기간 {health.period || "-"}</span>
        </div>
      </div>

      <div className="opinion-list">
        {health.evaluation_opinion_lines.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>

      <div className="domain-list">
        {health.domains.map((domain) => {
          const ratio = domain.max_score ? Math.round((domain.score / domain.max_score) * 100) : 0;
          return (
            <div key={domain.name} className="domain-card">
              <div className="domain-header">
                <strong>{domain.name}</strong>
                <span>
                  {domain.score} / {domain.max_score}
                </span>
              </div>
              <div className="industry-bar score-bar">
                <div style={{ width: `${ratio}%` }} />
              </div>
              <div className="domain-items">
                {domain.items.map((item) => (
                  <div key={item.label} className="domain-item">
                    <span>{item.label}</span>
                    <span>{item.value !== null ? `${item.value}${item.unit}` : "데이터 없음"}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
