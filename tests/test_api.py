import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import config


@pytest.fixture
def client():
    """TestClient พร้อม API_KEY ที่กำหนดไว้สำหรับ test"""
    with patch.object(config, "API_KEY", "test-key-123"):
        from api import app
        yield TestClient(app)


def _mock_price():
    price = MagicMock()
    price.scraped_at = datetime(2026, 6, 9, 10, 30, 0)
    price.gold_bar_buy = 45500.00
    price.gold_bar_sell = 45600.00
    price.gold_ornament_buy = 44850.00
    price.gold_ornament_sell = 46100.00
    price.source_url = "https://classic.goldtraders.or.th/default.aspx"
    return price


def test_latest_returns_200_with_valid_key(client):
    with patch("api.get_latest", return_value=_mock_price()):
        response = client.get("/api/latest", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["gold_bar_buy"] == 45500.00
    assert data["gold_bar_sell"] == 45600.00
    assert data["gold_ornament_buy"] == 44850.00
    assert data["gold_ornament_sell"] == 46100.00
    assert data["scraped_at"] == "2026-06-09 10:30:00"
    assert data["source_url"] == "https://classic.goldtraders.or.th/default.aspx"


def test_latest_returns_401_with_wrong_key(client):
    response = client.get("/api/latest", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_latest_returns_401_with_no_key(client):
    response = client.get("/api/latest")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_latest_returns_404_when_no_data(client):
    with patch("api.get_latest", return_value=None):
        response = client.get("/api/latest", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No gold price data available"
