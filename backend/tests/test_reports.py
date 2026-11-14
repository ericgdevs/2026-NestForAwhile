from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_manager_can_download_synthetic_report_without_client_identifiers(
    database, logged_in_client
):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            "/reports/donor",
            json={},
            cookies=logged_in_client(Role.WAREHOUSE_MANAGER).cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    with ZipFile(BytesIO(response.content)) as archive:
        document = archive.read("word/document.xml").decode()
    assert "Attribution" in document
    assert "Distribution totals" in document
    assert "Visit metrics" in document
    assert "Inventory and waste summary" in document
    assert "client" not in document.lower()
    assert "email" not in document.lower()
