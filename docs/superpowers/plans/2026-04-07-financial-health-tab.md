# 재무건전성 탭 개선 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엑셀 템플릿 기준(8개 지표, 100점 만점, AAA~B 6등급)으로 재무건전성 API와 탭 UI를 개선한다.

**Architecture:** `financial_health.py`에서 DB의 pre-computed 비율 지표(안정성지표·수익성지표·주요재무지표·활동성지표·현금흐름분석 섹션)를 읽어 8개 지표를 5개 영역으로 그룹화한 점수/등급 구조체를 반환한다. `company.html`의 `loadHealth()` 함수는 해당 응답을 받아 요약 카드 + 영역별 점수바 + 레이더 차트 + 세부 테이블을 렌더링한다.

**Tech Stack:** Python 3, SQLite, FastAPI, Jinja2, Chart.js (radar)

---

## DB 데이터 소스 요약

각 지표는 DB에 pre-computed된 섹션에서 읽는다. 각 period당 회사값·벤치마크 2행이 존재하므로 `ORDER BY id LIMIT 1`로 회사값만 취한다.

| 지표 | section | metric |
|------|---------|--------|
| 유동비율(%) | 안정성지표 | 유동비율(%) |
| 부채비율(%) | 안정성지표 | 부채비율(%) |
| 이자보상배율(배) | 수익성지표 | 이자보상배율(배) |
| 영업이익률(%) | 주요재무지표 | 매출액영업이익률(%) |
| ROE(%) | 수익성지표 | 자기자본순이익률(%) |
| 매출액증가율(%) | 주요재무지표 | 매출액증가율(%) |
| 매출채권회전일수 | 활동성지표 | 매출채권회전율(회) → 365/값 |
| 영업현금흐름(백만원) | 현금흐름분석 | 영업활동 현금흐름 |

---

## 파일 구조

| 파일 | 변경 유형 | 역할 |
|------|----------|------|
| `app/services/financial_health.py` | 전면 재작성 | 8개 지표 계산 + 점수/등급 반환 |
| `app/templates/company.html` | `loadHealth()` 교체 | 요약 카드 + 도메인 바 + 레이더 + 테이블 렌더링 |
| `tests/test_financial_health.py` | 신규 생성 | 점수 계산 로직 단위 테스트 |

---

## Task 1: `financial_health.py` 전면 재작성

**Files:**
- Modify: `app/services/financial_health.py`

- [ ] **Step 1: 파일 전체를 아래 내용으로 교체**

```python
"""재무건전성 지표 계산 서비스 — 엑셀 템플릿 기준 (8개 지표, 100점)."""

from typing import Optional
from app.database import get_db


# ─── 점수 계산 규칙 ──────────────────────────────────────────────────────────

def _score_current_ratio(v: float) -> int:
    """유동비율(%) 배점 20점."""
    if v >= 150: return 20
    if v >= 100: return 14
    if v >= 80:  return 8
    return 3

def _score_debt_ratio(v: float) -> int:
    """부채비율(%) 배점 15점. 낮을수록 좋음."""
    if v <= 100: return 15
    if v <= 150: return 11
    if v <= 200: return 6
    return 2

def _score_interest_coverage(v: float) -> int:
    """이자보상배율(배) 배점 10점."""
    if v >= 5: return 10
    if v >= 2: return 7
    if v >= 1: return 4
    return 0

def _score_operating_margin(v: float) -> int:
    """영업이익률(%) 배점 20점."""
    if v >= 7: return 20
    if v >= 3: return 14
    if v >= 0: return 8
    return 0

def _score_roe(v: float) -> int:
    """ROE(%) 배점 10점."""
    if v >= 10: return 10
    if v >= 5:  return 7
    if v >= 0:  return 4
    return 0

def _score_revenue_growth(v: float) -> int:
    """매출액증가율(%) 배점 10점."""
    if v >= 10:  return 10
    if v >= 0:   return 7
    if v >= -5:  return 4
    return 0

def _score_ar_days(v: float) -> int:
    """매출채권회전일수(일) 배점 8점. 낮을수록 좋음."""
    if v <= 45:  return 8
    if v <= 90:  return 5
    if v <= 120: return 2
    return 0

def _score_operating_cf(v: float) -> int:
    """영업현금흐름(백만원) 배점 7점."""
    if v > 0:    return 7
    if v > -100: return 4
    return 0

def _item_grade(score: int, max_score: int) -> str:
    """개별 항목 등급 (A/B/C/D)."""
    if max_score == 0:
        return "N/A"
    ratio = score / max_score
    if ratio >= 0.8: return "A (양호)"
    if ratio >= 0.6: return "B (보통)"
    if ratio >= 0.4: return "C (주의)"
    return "D (위험)"

def _total_grade(total: int) -> str:
    if total >= 85: return "AAA"
    if total >= 75: return "AA"
    if total >= 65: return "A"
    if total >= 55: return "BBB"
    if total >= 45: return "BB"
    return "B"

def _recommendation(total: int) -> str:
    if total >= 75: return "✅ 거래 계속 (정상)"
    if total >= 55: return "⚠️ 조건부 거래 (모니터링 강화)"
    return "🚫 거래 재검토 필요"


# ─── DB 조회 헬퍼 ────────────────────────────────────────────────────────────

def _get_ratio(conn, import_id: int, section: str, metric: str, period: str) -> Optional[float]:
    """period 내 첫 번째 행(회사값)을 반환. 없으면 None."""
    row = conn.execute(
        "SELECT value_num FROM report_values "
        "WHERE import_id=? AND section=? AND metric=? AND period=? AND value_num IS NOT NULL "
        "ORDER BY id LIMIT 1",
        (import_id, section, metric, period),
    ).fetchone()
    return row["value_num"] if row else None


def _latest_period(conn, import_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT period FROM report_values "
        "WHERE import_id=? AND period != '-' ORDER BY period DESC LIMIT 1",
        (import_id,),
    ).fetchone()
    return row["period"] if row else None


# ─── 메인 계산 함수 ──────────────────────────────────────────────────────────

def calculate_health(company_id: int) -> dict:
    """8개 지표 100점 만점 재무건전성 평가."""
    with get_db() as conn:
        period = _latest_period(conn, company_id)
        if not period:
            return {"error": "데이터 없음", "domains": [], "total_score": 0, "grade": "-", "period": ""}

        def get(section, metric):
            return _get_ratio(conn, company_id, section, metric, period)

        # 8개 지표값 수집
        current_ratio   = get("안정성지표",   "유동비율(%)")
        debt_ratio      = get("안정성지표",   "부채비율(%)")
        interest_cov    = get("수익성지표",   "이자보상배율(배)")
        op_margin       = get("주요재무지표", "매출액영업이익률(%)")
        roe             = get("수익성지표",   "자기자본순이익률(%)")
        rev_growth      = get("주요재무지표", "매출액증가율(%)")
        ar_turnover     = get("활동성지표",   "매출채권회전율(회)")
        op_cf           = get("현금흐름분석", "영업활동 현금흐름")

    # 매출채권회전율 → 회전일수 변환
    ar_days = round(365 / ar_turnover, 1) if ar_turnover and ar_turnover > 0 else None

    def make_item(label, value, unit, benchmark, max_score, score_fn):
        if value is None:
            return {
                "label": label, "value": None, "unit": unit,
                "benchmark": benchmark, "max_score": max_score,
                "score": 0, "item_grade": "N/A",
            }
        score = score_fn(value)
        return {
            "label": label,
            "value": round(value, 2),
            "unit": unit,
            "benchmark": benchmark,
            "max_score": max_score,
            "score": score,
            "item_grade": _item_grade(score, max_score),
        }

    domains = [
        {
            "name": "안전성",
            "max_score": 45,
            "items": [
                make_item("유동비율",     current_ratio, "%",  "100% 이상", 20, _score_current_ratio),
                make_item("부채비율",     debt_ratio,    "%",  "150% 이하", 15, _score_debt_ratio),
                make_item("이자보상배율", interest_cov,  "배", "3배 이상",  10, _score_interest_coverage),
            ],
        },
        {
            "name": "수익성",
            "max_score": 30,
            "items": [
                make_item("영업이익률", op_margin, "%", "5% 이상", 20, _score_operating_margin),
                make_item("ROE",        roe,       "%", "8% 이상", 10, _score_roe),
            ],
        },
        {
            "name": "성장성",
            "max_score": 10,
            "items": [
                make_item("매출액증가율", rev_growth, "%", "5% 이상", 10, _score_revenue_growth),
            ],
        },
        {
            "name": "활동성",
            "max_score": 8,
            "items": [
                make_item("매출채권회전일수", ar_days, "일", "60일 이하", 8, _score_ar_days),
            ],
        },
        {
            "name": "현금흐름",
            "max_score": 7,
            "items": [
                make_item("영업현금흐름", op_cf, "백만원", "양(+)값", 7, _score_operating_cf),
            ],
        },
    ]

    # 도메인별 점수 합산
    for d in domains:
        d["score"] = sum(i["score"] for i in d["items"])

    total = sum(d["score"] for d in domains)

    return {
        "period": period,
        "total_score": total,
        "grade": _total_grade(total),
        "recommendation": _recommendation(total),
        "domains": domains,
    }
```

- [ ] **Step 2: 서버 재시작 후 API 수동 확인**

```bash
cd C:\Users\user\Desktop\PROJECT_SEHWAN
python -c "
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.services.financial_health import calculate_health
result = calculate_health(292)
print('grade:', result['grade'])
print('total:', result['total_score'])
for d in result['domains']:
    print(d['name'], d['score'], '/', d['max_score'])
    for item in d['items']:
        print('  ', item['label'], item['value'], '->', item['score'], item['item_grade'])
"
```

기대 출력 예시:
```
grade: BBB
total: 53
안전성 17 / 45
  유동비율 80.49 -> 8 C (주의)
  부채비율 248.8 -> 2 D (위험)
  이자보상배율 1.65 -> 4 C (주의)
수익성 ...
```

- [ ] **Step 3: 커밋**

```bash
git add app/services/financial_health.py
git commit -m "feat: financial_health 서비스를 8개 지표 100점 체계로 전면 개편"
```

---

## Task 2: 통합 테스트 작성

**Files:**
- Create: `tests/test_financial_health.py`

- [ ] **Step 1: 테스트 파일 생성**

```python
"""financial_health 서비스 단위·통합 테스트."""
import pytest
from app.services.financial_health import (
    _score_current_ratio,
    _score_debt_ratio,
    _score_interest_coverage,
    _score_operating_margin,
    _score_roe,
    _score_revenue_growth,
    _score_ar_days,
    _score_operating_cf,
    _total_grade,
    _recommendation,
    calculate_health,
)


class TestScoringFunctions:
    def test_current_ratio_tiers(self):
        assert _score_current_ratio(160) == 20
        assert _score_current_ratio(120) == 14
        assert _score_current_ratio(85)  == 8
        assert _score_current_ratio(50)  == 3

    def test_debt_ratio_tiers(self):
        assert _score_debt_ratio(80)  == 15
        assert _score_debt_ratio(130) == 11
        assert _score_debt_ratio(180) == 6
        assert _score_debt_ratio(250) == 2

    def test_interest_coverage_tiers(self):
        assert _score_interest_coverage(6.0) == 10
        assert _score_interest_coverage(3.0) == 7
        assert _score_interest_coverage(1.5) == 4
        assert _score_interest_coverage(0.5) == 0

    def test_operating_margin_tiers(self):
        assert _score_operating_margin(8.0)  == 20
        assert _score_operating_margin(5.0)  == 14
        assert _score_operating_margin(1.0)  == 8
        assert _score_operating_margin(-1.0) == 0

    def test_roe_tiers(self):
        assert _score_roe(12.0) == 10
        assert _score_roe(7.0)  == 7
        assert _score_roe(3.0)  == 4
        assert _score_roe(-1.0) == 0

    def test_revenue_growth_tiers(self):
        assert _score_revenue_growth(15.0) == 10
        assert _score_revenue_growth(5.0)  == 7
        assert _score_revenue_growth(-3.0) == 4
        assert _score_revenue_growth(-8.0) == 0

    def test_ar_days_tiers(self):
        assert _score_ar_days(30)  == 8
        assert _score_ar_days(60)  == 5
        assert _score_ar_days(100) == 2
        assert _score_ar_days(130) == 0

    def test_operating_cf_tiers(self):
        assert _score_operating_cf(500)  == 7
        assert _score_operating_cf(-50)  == 4
        assert _score_operating_cf(-200) == 0

    def test_total_grade_boundaries(self):
        assert _total_grade(90) == "AAA"
        assert _total_grade(80) == "AA"
        assert _total_grade(70) == "A"
        assert _total_grade(60) == "BBB"
        assert _total_grade(50) == "BB"
        assert _total_grade(40) == "B"

    def test_recommendation_boundaries(self):
        assert "거래 계속"   in _recommendation(75)
        assert "조건부 거래" in _recommendation(55)
        assert "재검토"      in _recommendation(44)


class TestCalculateHealth:
    def test_returns_expected_keys(self):
        result = calculate_health(292)
        assert "period"         in result
        assert "total_score"    in result
        assert "grade"          in result
        assert "recommendation" in result
        assert "domains"        in result

    def test_domains_structure(self):
        result = calculate_health(292)
        names = [d["name"] for d in result["domains"]]
        assert names == ["안전성", "수익성", "성장성", "활동성", "현금흐름"]

    def test_total_score_equals_domain_sum(self):
        result = calculate_health(292)
        domain_sum = sum(d["score"] for d in result["domains"])
        assert result["total_score"] == domain_sum

    def test_score_within_max(self):
        result = calculate_health(292)
        for d in result["domains"]:
            assert 0 <= d["score"] <= d["max_score"]
            for item in d["items"]:
                assert 0 <= item["score"] <= item["max_score"]

    def test_invalid_company_returns_error(self):
        result = calculate_health(999999)
        assert "error" in result
```

- [ ] **Step 2: 테스트 실행**

```bash
cd C:\Users\user\Desktop\PROJECT_SEHWAN
python -m pytest tests/test_financial_health.py -v
```

기대 출력:
```
PASSED tests/test_financial_health.py::TestScoringFunctions::test_current_ratio_tiers
...
PASSED tests/test_financial_health.py::TestCalculateHealth::test_returns_expected_keys
...
15 passed in X.XXs
```

- [ ] **Step 3: 커밋**

```bash
git add tests/test_financial_health.py
git commit -m "test: financial_health 서비스 단위·통합 테스트 추가"
```

---

## Task 3: `company.html` — `loadHealth()` 함수 교체

**Files:**
- Modify: `app/templates/company.html` (loadHealth 함수 전체)

- [ ] **Step 1: `loadHealth()` 함수를 아래 내용으로 교체**

`company.html` 파일에서 아래 범위를 찾아 교체한다:
```
// ─── 재무건전성 탭 ───────────────────────────────────────────
async function loadHealth() {
  ...  (기존 함수 전체)
}
```

교체할 새 함수:

```javascript
// ─── 재무건전성 탭 ───────────────────────────────────────────
async function loadHealth() {
  const tab = document.getElementById('tab-health');
  tab.dataset.loaded = '1';
  tab.innerHTML = '<div class="text-center py-12 text-gray-400">분석 중...</div>';

  const res = await fetch(`/api/companies/${CID}/health`);
  healthData = await res.json();

  if (healthData.error) {
    tab.innerHTML = `<div class="text-center py-8 text-gray-400">${healthData.error}</div>`;
    return;
  }

  // ── 등급별 색상 매핑 ──────────────────────────────────────
  const gradeStyle = {
    'AAA': { badge: 'bg-emerald-100 text-emerald-800 border-emerald-300', bar: '#10b981' },
    'AA':  { badge: 'bg-green-100 text-green-800 border-green-300',       bar: '#22c55e' },
    'A':   { badge: 'bg-blue-100 text-blue-800 border-blue-300',          bar: '#3b82f6' },
    'BBB': { badge: 'bg-yellow-100 text-yellow-800 border-yellow-300',    bar: '#eab308' },
    'BB':  { badge: 'bg-orange-100 text-orange-800 border-orange-300',    bar: '#f97316' },
    'B':   { badge: 'bg-red-100 text-red-800 border-red-300',             bar: '#ef4444' },
  };
  const gs = gradeStyle[healthData.grade] || { badge: 'bg-gray-100 text-gray-700 border-gray-300', bar: '#6b7280' };

  const itemGradeColor = {
    'A (양호)': 'text-emerald-600', 'B (보통)': 'text-blue-600',
    'C (주의)': 'text-yellow-600',  'D (위험)': 'text-red-600', 'N/A': 'text-gray-400',
  };

  const domainColors = ['#3b82f6','#8b5cf6','#10b981','#f59e0b','#ef4444'];

  // ── 영역별 레이더 라벨·값 ─────────────────────────────────
  const radarLabels = healthData.domains.map(d => `${d.name}\n(${d.score}/${d.max_score})`);
  const radarValues = healthData.domains.map(d =>
    d.max_score > 0 ? Math.round(d.score / d.max_score * 100) : 0
  );

  // ── HTML 렌더링 ───────────────────────────────────────────
  tab.innerHTML = `
    <!-- 종합 요약 카드 -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full border-2 ${gs.badge} text-3xl font-bold">
            ${healthData.grade}
          </div>
          <div class="mt-1 text-xs text-gray-400">${healthData.period} 기준</div>
        </div>
        <div class="flex-1">
          <div class="flex items-baseline gap-2 mb-1">
            <span class="text-2xl font-bold text-gray-900">${healthData.total_score}점</span>
            <span class="text-sm text-gray-400">/ 100점</span>
          </div>
          <div class="text-sm font-medium text-gray-700 mb-3">${healthData.recommendation}</div>
          <!-- 총점 프로그레스 바 -->
          <div class="w-full bg-gray-100 rounded-full h-2.5">
            <div class="h-2.5 rounded-full transition-all duration-700"
                 style="width:${healthData.total_score}%; background:${gs.bar}"></div>
          </div>
        </div>
        <!-- 등급 기준 범례 -->
        <div class="hidden md:block text-xs text-gray-400 space-y-0.5">
          <div><span class="font-semibold text-emerald-600">AAA</span> 85점↑ 최우량</div>
          <div><span class="font-semibold text-green-600">AA</span> 75점↑ 우량</div>
          <div><span class="font-semibold text-blue-600">A</span> 65점↑ 양호</div>
          <div><span class="font-semibold text-yellow-600">BBB</span> 55점↑ 보통</div>
          <div><span class="font-semibold text-orange-500">BB</span> 45점↑ 주의</div>
          <div><span class="font-semibold text-red-600">B</span> 44점↓ 위험</div>
        </div>
      </div>
    </div>

    <!-- 레이더 차트 + 영역별 점수 바 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-base font-semibold text-gray-700 mb-4">영역별 건전성</h3>
        <div class="flex justify-center"><canvas id="radarCanvas" width="300" height="300"></canvas></div>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-base font-semibold text-gray-700 mb-4">영역별 점수</h3>
        <div class="space-y-4" id="domainBars"></div>
      </div>
    </div>

    <!-- 세부 지표 테이블 -->
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <h3 class="text-base font-semibold text-gray-700 mb-4">세부 지표</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b-2 border-gray-200 bg-gray-50">
              <th class="text-left py-2.5 px-3 font-semibold text-gray-500">영역</th>
              <th class="text-left py-2.5 px-3 font-semibold text-gray-500">지표</th>
              <th class="text-right py-2.5 px-3 font-semibold text-gray-500">값</th>
              <th class="text-center py-2.5 px-3 font-semibold text-gray-500">벤치마크</th>
              <th class="text-center py-2.5 px-3 font-semibold text-gray-500">점수</th>
              <th class="text-center py-2.5 px-3 font-semibold text-gray-500">등급</th>
            </tr>
          </thead>
          <tbody id="healthTableBody"></tbody>
        </table>
      </div>
    </div>
  `;

  // ── 영역별 점수 바 렌더링 ─────────────────────────────────
  const barsEl = document.getElementById('domainBars');
  healthData.domains.forEach((d, i) => {
    const pct = d.max_score > 0 ? Math.round(d.score / d.max_score * 100) : 0;
    const color = domainColors[i] || '#6b7280';
    barsEl.innerHTML += `
      <div>
        <div class="flex justify-between text-xs text-gray-600 mb-1">
          <span class="font-medium">${d.name}</span>
          <span>${d.score} / ${d.max_score}점</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-3">
          <div class="h-3 rounded-full transition-all duration-700"
               style="width:${pct}%; background:${color}"></div>
        </div>
      </div>
    `;
  });

  // ── 세부 테이블 렌더링 ────────────────────────────────────
  const tbody = document.getElementById('healthTableBody');
  healthData.domains.forEach(d => {
    d.items.forEach((item, idx) => {
      const gc = itemGradeColor[item.item_grade] || 'text-gray-500';
      const scoreColor = item.score === item.max_score
        ? 'text-emerald-600 font-bold'
        : item.score === 0
          ? 'text-red-500'
          : 'text-gray-700';
      const domainCell = idx === 0
        ? `<td class="py-2.5 px-3 font-medium text-gray-700" rowspan="${d.items.length}">${d.name}</td>`
        : '';
      const valDisplay = item.value !== null
        ? `${item.value.toLocaleString('ko-KR')}${item.unit}`
        : '-';
      tbody.innerHTML += `
        <tr class="border-b border-gray-100 hover:bg-gray-50/50">
          ${domainCell}
          <td class="py-2.5 px-3 text-gray-700">${item.label}</td>
          <td class="py-2.5 px-3 text-right font-mono text-gray-800">${valDisplay}</td>
          <td class="py-2.5 px-3 text-center text-gray-400 text-xs">${item.benchmark}</td>
          <td class="py-2.5 px-3 text-center ${scoreColor}">${item.score}<span class="text-gray-300 text-xs">/${item.max_score}</span></td>
          <td class="py-2.5 px-3 text-center text-xs font-medium ${gc}">${item.item_grade}</td>
        </tr>
      `;
    });
  });

  // ── 레이더 차트 ──────────────────────────────────────────
  const ctx = document.getElementById('radarCanvas').getContext('2d');
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: radarLabels,
      datasets: [{
        label: '건전성 점수(%)',
        data: radarValues,
        backgroundColor: 'rgba(59,130,246,0.15)',
        borderColor: 'rgba(59,130,246,0.8)',
        pointBackgroundColor: domainColors,
        pointRadius: 5,
        borderWidth: 2,
      }]
    },
    options: {
      scales: {
        r: {
          beginAtZero: true, max: 100, min: 0,
          ticks: { stepSize: 25, font: { size: 9 }, display: false },
          pointLabels: { font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,0.08)' },
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: c => `${c.raw}% 달성` } },
      },
    }
  });
}
```

- [ ] **Step 2: 브라우저에서 재무건전성 탭 확인**

서버 실행 후 임의 기업 상세 페이지 → 재무건전성 탭 클릭.

확인 항목:
- 종합 등급 뱃지(AAA~B)와 점수가 표시되는가
- 거래 권고 문구가 표시되는가
- 총점 프로그레스 바가 채워지는가
- 5개 영역 점수 바가 표시되는가
- 레이더 차트가 그려지는가
- 세부 테이블에 8개 지표 행이 있는가
- 값이 없는 지표는 "-"로 표시되는가

- [ ] **Step 3: 커밋**

```bash
git add app/templates/company.html
git commit -m "feat: 재무건전성 탭 UI 개선 — 8개 지표 100점 체계 + AAA~B 등급 표시"
```

---

## 완료 기준 체크리스트

- [ ] `calculate_health(292)` 호출 시 `total_score`, `grade`, `domains` 5개 포함 응답 반환
- [ ] 모든 pytest 테스트 통과
- [ ] 재무건전성 탭에서 요약 카드, 점수 바, 레이더, 테이블 4개 섹션 모두 렌더링
- [ ] 데이터 없는 기업에서 에러 메시지 표시 (화면 깨짐 없음)
