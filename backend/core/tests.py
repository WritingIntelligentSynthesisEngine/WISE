# core/tests.py
from django.test import TestCase


class CoreTestCase(TestCase):
    """核心 API 测试用例"""

    def test_openapi_docs_available(self) -> None:
        """测试 OpenAPI 文档是否可用"""
        response = self.client.get("/api/docs")
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_available(self) -> None:
        """测试 OpenAPI Schema 是否可用"""
        response = self.client.get("/api/openapi.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("openapi", data)
        self.assertIn("info", data)
        self.assertIn("paths", data)

    def test_status_endpoint(self) -> None:
        """测试状态检查端点"""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("message", data)
        self.assertIn("timestamp", data)
