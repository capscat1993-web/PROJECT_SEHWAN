"use client";

import { getClientApiBaseUrl } from "@/lib/api";

type HealthItem = {
  label: string;
  score: number;
  max_score: number;
  configured_max_score?: number;
  value: number | null;
  unit: string;
  benchmark: string;
  item_grade: string;
  is_missing?: boolean;
};

type HealthDomain = {
  name: string;
  score: number;
  max_score: number;
  items: HealthItem[];
};

type HealthData = {
  grade: string;
  total_score: number;
  recommendation: string;
  period: string;
  evaluation_opinion_lines: string[];
  grade_note?: string;
  data_note?: string;
  data_completeness_pct?: number;
  domains: HealthDomain[];
};

function itemGradeColor(grade: string): string {
  if (grade.startsWith("A")) return "item-grade-a";
  if (grade.startsWith("B")) return "item-grade-b";
  if (grade.startsWith("C")) return "item-grade-c";
  if (grade.startsWith("D")) return "item-grade-d";
  return "item-grade-na";
}

function gradeColor(grade: string): string {
  if (grade === "AAA" || grade === "AA") return "grade-badge grade-badge--green";
  if (grade === "A") return "grade-badge grade-badge--blue";
  if (grade === "BBB") return "grade-badge grade-badge--amber";
  if (grade === "BB") return "grade-badge grade-badge--orange";
  return "grade-badge grade-badge--red";
}

export function HealthPanel({
  companyId,
  health,
}: Readonly<{
  companyId: number;
  health: HealthData;
}>) {
  const exportUrl = `${getClientApiBaseUrl()}/api/companies/${companyId}/health/export`;

  return (
    <div className="panel report-panel health-panel">
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
        <div className={gradeColor(health.grade)}>{health.grade}</div>
        <div>
          <strong>{health.total_score}점</strong>
          <p>{health.recommendation}</p>
          <span className="subtle">기준기간 {health.period || "-"}</span>
          {health.data_completeness_pct !== undefined && health.data_completeness_pct < 100 && (
            <span className="completeness-badge">데이터 {health.data_completeness_pct}% 확보</span>
          )}
        </div>
      </div>

      {health.grade_note && (
        <div className="health-alert">
          <span className="health-alert-icon">⚠</span>
          {health.grade_note}
        </div>
      )}

      <div className="opinion-list">
        {health.evaluation_opinion_lines.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>

      <div className="domain-list">
        {health.domains.map((domain) => {
          const isDataMissing = domain.max_score === 0;
          const ratio = domain.max_score ? Math.round((domain.score / domain.max_score) * 100) : 0;
          return (
            <div key={domain.name} className="domain-card">
              <div className="domain-header">
                <strong>{domain.name}</strong>
                {isDataMissing ? (
                  <span className="completeness-badge">데이터 없음</span>
                ) : (
                  <span>
                    {domain.score} / {domain.max_score}점
                  </span>
                )}
              </div>
              {!isDataMissing && (
                <div className="industry-bar score-bar">
                  <div style={{ width: `${ratio}%` }} />
                </div>
              )}
              <div className="domain-items">
                {domain.items.map((item) => (
                  <div key={item.label} className="domain-item">
                    <div className="domain-item-top">
                      <span className="domain-item-label">{item.label}</span>
                      <span className={`item-grade-badge ${itemGradeColor(item.item_grade)}`}>
                        {item.item_grade}
                      </span>
                    </div>
                    <div className="domain-item-bottom">
                      <span className="domain-item-value">
                        {item.value !== null ? `${item.value}${item.unit}` : "데이터 없음"}
                      </span>
                      <span className="domain-item-benchmark">기준: {item.benchmark}</span>
                      {!isDataMissing && (
                        <span className="domain-item-score">{item.score}/{item.max_score}점</span>
                      )}
                    </div>
                    {item.max_score > 0 && (
                      <div className="item-score-bar">
                        <div
                          style={{ width: `${Math.round((item.score / item.max_score) * 100)}%` }}
                          className={`item-score-fill ${itemGradeColor(item.item_grade)}`}
                        />
                      </div>
                    )}
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
