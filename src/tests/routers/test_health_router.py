import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock
from flask import Flask
from sqlalchemy.exc import OperationalError

from routers import health_router


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()

    @contextmanager
    def fake_get_db():
        yield db

    monkeypatch.setattr(health_router, "get_db", fake_get_db)
    return db


@pytest.fixture
def client():
    # App mínima: não importa main.py, que exige banco no import
    app = Flask(__name__)
    app.register_blueprint(health_router.bp)
    return app.test_client()


def test_health_returns_200_without_touching_database(client, mock_db):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    mock_db.execute.assert_not_called()


def test_ready_returns_200_when_database_is_up(client, mock_db):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}
    mock_db.execute.assert_called_once()


def test_ready_returns_503_when_database_is_down(client, mock_db):
    mock_db.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("connection refused")
    )

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "not ready"
    assert "connection refused" in body["reason"]
