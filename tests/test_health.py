"""Health API contract tests."""

from backend.app.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_service_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "NorseAI API",
        "version": "0.1.0",
        "environment": "test",
    }


def test_openapi_document_is_disabled_in_test_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 404


def test_swagger_and_root_openapi_are_available_when_docs_are_enabled(test_settings) -> None:
    settings = test_settings.model_copy(update={"docs_enabled": True})

    with TestClient(create_app(settings)) as documented:
        docs = documented.get("/docs")
        root_schema = documented.get("/openapi.json")
        versioned_schema = documented.get("/api/v1/openapi.json")

    assert docs.status_code == 200
    assert "Swagger UI" in docs.text
    assert "/docs-assets/swagger-ui-bundle.js" in docs.text
    assert "cdn.jsdelivr.net" not in docs.text
    assert "script-src 'self' 'unsafe-inline'" in docs.headers["content-security-policy"]
    assert root_schema.status_code == 200
    assert root_schema.json()["openapi"].startswith("3.")
    assert versioned_schema.status_code == 200
    assert root_schema.json() == versioned_schema.json()
