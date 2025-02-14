from django.test import RequestFactory, TestCase
from fecfiler.openapi.views import FecfileSpectacularSwaggerView


class OpenApiTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_api_docs_endpoint(self):
        request = self.factory.get("/api/docs/")
        response = FecfileSpectacularSwaggerView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["nonce"] in response["Content-Security-Policy"])
