import pytest
from unittest.mock import MagicMock, patch
from scraper import parse_gold_prices, scrape


SAMPLE_HTML = """
<html>
<body>
<table>
  <tr>
    <td>ทองคำแท่ง 96.5%</td>
    <td>ซื้อ</td>
    <td>45,500.00</td>
    <td>ขาย</td>
    <td>45,600.00</td>
  </tr>
  <tr>
    <td>ทองรูปพรรณ 96.5%</td>
    <td>ซื้อ</td>
    <td>44,650.00</td>
    <td>ขาย</td>
    <td>45,950.00</td>
  </tr>
</table>
</body>
</html>
"""


def test_parse_gold_prices_returns_correct_values():
    result = parse_gold_prices(SAMPLE_HTML)
    assert result is not None
    assert result["gold_bar_buy"] == 45500.00
    assert result["gold_bar_sell"] == 45600.00
    assert result["gold_ornament_buy"] == 44650.00
    assert result["gold_ornament_sell"] == 45950.00


def test_parse_gold_prices_returns_none_on_invalid_html():
    result = parse_gold_prices("<html><body>No data here</body></html>")
    assert result is None


def test_scrape_returns_data_on_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_HTML
    with patch("scraper.requests.get", return_value=mock_response):
        result = scrape()
    assert result is not None
    assert result["gold_bar_buy"] == 45500.00


def test_scrape_retries_on_connection_error():
    with patch("scraper.requests.get", side_effect=Exception("Connection error")) as mock_get:
        with patch("scraper.time.sleep"):
            result = scrape()
    assert result is None
    assert mock_get.call_count == 3  # retry 3 ครั้ง
