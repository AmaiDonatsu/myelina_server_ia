import pytest


def test_404_html_for_browser_navigation(client):
    # Standard browser navigation (Accept: text/html or default) to non-existent route
    response = client.get("/pagina-que-no-existe", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "404 - Página no encontrada" in response.text
    assert "/pagina-que-no-existe" in response.text


def test_404_json_for_api_requests(client):
    # API route that does not exist
    response = client.get("/api/v1/auth/non-existent-endpoint")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "detail" in data
    assert data["path"] == "/api/v1/auth/non-existent-endpoint"


def test_404_direct_route(client):
    response = client.get("/404")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "404" in response.text
