from django.test import Client, TestCase

from reports.services.financial_health import calculate_health


class ApiSmokeTests(TestCase):
    databases = {"default"}

    def setUp(self):
        self.client = Client()

    def test_root_returns_platform_metadata(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_overview_endpoint_returns_summary(self):
        response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("total_companies", payload)
        self.assertIn("top_industries", payload)

    def test_company_dashboard_returns_payload(self):
        response = self.client.get("/api/companies/400/dashboard")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("company", payload)
        self.assertIn("tables", payload)
        self.assertIn("key_metrics", payload)
        self.assertTrue(payload["key_metrics"]["periods"])
        self.assertIn("주요재무지표", payload["tables"])
        self.assertEqual(payload["key_metrics"]["periods"], ["2019.12", "2020.12", "2021.12"])
        self.assertNotIn("손익계산서", payload["tables"])


class FinancialHealthSmokeTests(TestCase):
    databases = {"default"}

    def test_health_service_returns_error_for_missing_company(self):
        result = calculate_health(999999999)
        self.assertIn("error", result)

    def test_health_service_uses_cashflow_fallback_when_raw_cashflow_is_missing(self):
        result = calculate_health(400)
        cashflow_domain = next(domain for domain in result["domains"] if domain["name"] == "현금흐름")
        cashflow_item = cashflow_domain["items"][0]
        self.assertFalse(cashflow_item["is_missing"])
        self.assertIsNotNone(cashflow_item["value"])
