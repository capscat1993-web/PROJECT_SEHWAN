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
