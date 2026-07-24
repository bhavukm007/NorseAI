"""Health API contract tests."""

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
