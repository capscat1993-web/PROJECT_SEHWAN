"""financial_health 서비스 단위·통합 테스트."""

import sqlite3

from app.services.financial_health import (
    _cap_grade,
    _recommendation,
    _score_ar_days,
    _score_current_ratio,
    _score_debt_ratio,
    _score_interest_coverage,
    _score_operating_cf,
    _score_operating_margin,
    _score_revenue_growth,
    _score_roe,
    _total_grade,
    calculate_health,
)


def _first_company_with_missing_cashflow() -> int:
    conn = sqlite3.connect("reports.db")
    try:
        ids = [row[0] for row in conn.execute("select id from report_imports order by id").fetchall()]
    finally:
        conn.close()

    for company_id in ids:
        result = calculate_health(company_id)
        if result.get("data_note"):
            return company_id
    raise AssertionError("현금흐름 데이터가 없는 테스트 대상 회사를 찾지 못했습니다.")


class TestScoringFunctions:
    def test_current_ratio_tiers(self):
        assert _score_current_ratio(160) == 20
        assert _score_current_ratio(120) == 14
        assert _score_current_ratio(85) == 8
        assert _score_current_ratio(50) == 3

    def test_debt_ratio_tiers(self):
        assert _score_debt_ratio(80) == 15
        assert _score_debt_ratio(130) == 11
        assert _score_debt_ratio(180) == 6
        assert _score_debt_ratio(250) == 2

    def test_interest_coverage_tiers(self):
        assert _score_interest_coverage(6.0) == 10
        assert _score_interest_coverage(3.0) == 7
        assert _score_interest_coverage(1.5) == 4
        assert _score_interest_coverage(0.5) == 0

    def test_operating_margin_tiers(self):
        assert _score_operating_margin(8.0) == 20
        assert _score_operating_margin(5.0) == 14
        assert _score_operating_margin(1.0) == 8
        assert _score_operating_margin(-1.0) == 0

    def test_roe_tiers(self):
        assert _score_roe(12.0) == 10
        assert _score_roe(7.0) == 7
        assert _score_roe(3.0) == 4
        assert _score_roe(-1.0) == 0

    def test_revenue_growth_tiers(self):
        assert _score_revenue_growth(15.0) == 10
        assert _score_revenue_growth(5.0) == 7
        assert _score_revenue_growth(-3.0) == 4
        assert _score_revenue_growth(-8.0) == 0

    def test_ar_days_tiers(self):
        assert _score_ar_days(30) == 8
        assert _score_ar_days(60) == 5
        assert _score_ar_days(100) == 2
        assert _score_ar_days(130) == 0

    def test_operating_cf_tiers(self):
        assert _score_operating_cf(500) == 7
        assert _score_operating_cf(-50) == 4
        assert _score_operating_cf(-200) == 0

    def test_total_grade_boundaries(self):
        assert _total_grade(90) == "AAA"
        assert _total_grade(80) == "AA"
        assert _total_grade(70) == "A"
        assert _total_grade(60) == "BBB"
        assert _total_grade(50) == "BB"
        assert _total_grade(40) == "B"

    def test_recommendation_boundaries(self):
        assert "거래 계속" in _recommendation(75)
        assert "조건부 거래" in _recommendation(55)
        assert "재검토" in _recommendation(44)

    def test_grade_cap(self):
        assert _cap_grade("AAA", "A") == "A"
        assert _cap_grade("AA", "A") == "A"
        assert _cap_grade("A", "A") == "A"
        assert _cap_grade("BBB", "A") == "BBB"


class TestCalculateHealth:
    def test_returns_expected_keys(self):
        result = calculate_health(292)
        assert "period" in result
        assert "total_score" in result
        assert "recommendation" in result
        assert "domains" in result
        assert "raw_score" in result
        assert "total_possible_score" in result
        assert "configured_total_score" in result
        assert "data_completeness_pct" in result
        assert "evaluation_opinion_lines" in result

    def test_domains_structure(self):
        result = calculate_health(292)
        names = [d["name"] for d in result["domains"]]
        assert names == ["안전성", "수익성", "성장성", "활동성", "현금흐름"]

    def test_raw_score_equals_domain_sum(self):
        result = calculate_health(292)
        domain_sum = sum(d["score"] for d in result["domains"])
        assert result["raw_score"] == domain_sum

    def test_total_possible_equals_domain_max_sum(self):
        result = calculate_health(292)
        domain_max_sum = sum(d["max_score"] for d in result["domains"])
        assert result["total_possible_score"] == domain_max_sum

    def test_normalized_total_uses_available_scores(self):
        result = calculate_health(292)
        if result["total_possible_score"] > 0:
            expected = round(result["raw_score"] / result["total_possible_score"] * 100)
            assert result["total_score"] == expected

    def test_score_within_max(self):
        result = calculate_health(292)
        for domain in result["domains"]:
            assert 0 <= domain["score"] <= domain["configured_max_score"]
            assert 0 <= domain["max_score"] <= domain["configured_max_score"]
            for item in domain["items"]:
                assert 0 <= item["score"] <= item["configured_max_score"]
                assert 0 <= item["max_score"] <= item["configured_max_score"]

    def test_missing_cashflow_is_excluded_and_grade_is_capped(self):
        result = calculate_health(_first_company_with_missing_cashflow())
        cashflow = next(d for d in result["domains"] if d["name"] == "현금흐름")
        item = cashflow["items"][0]
        assert item["is_missing"] is True
        assert item["max_score"] == 0
        assert item["configured_max_score"] == 7
        assert item["item_grade"] == "N/A"
        assert result["data_completeness_pct"] < 100
        assert result["data_note"]
        assert _cap_grade(result["uncapped_grade"], "A") == result["grade"]

    def test_evaluation_opinion_has_two_or_three_lines(self):
        result = calculate_health(292)
        assert 2 <= len(result["evaluation_opinion_lines"]) <= 3
        assert all(isinstance(line, str) and line for line in result["evaluation_opinion_lines"])

    def test_invalid_company_returns_error(self):
        result = calculate_health(999999)
        assert "error" in result
