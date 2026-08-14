from fastapi.testclient import TestClient

from web.main import app


def test_openapi_schema_loads_without_starting_lifespan() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "MeterLink Industrial"
