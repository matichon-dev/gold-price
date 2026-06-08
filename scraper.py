import logging
import time

import requests
from bs4 import BeautifulSoup

URL = "https://classic.goldtraders.or.th/default.aspx"
RETRY_COUNT = 3
RETRY_DELAY = 5  # วินาที

logger = logging.getLogger(__name__)


def parse_gold_prices(html: str) -> dict | None:
    """
    Parse ราคาทองจาก HTML string
    คืนค่า dict หรือ None ถ้า parse ไม่ได้
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        prices = {}

        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            text = " ".join(c.get_text(strip=True) for c in cells)

            if "ทองคำแท่ง" in text and len(cells) >= 5:
                prices["gold_bar_buy"] = _parse_price(cells[2].get_text(strip=True))
                prices["gold_bar_sell"] = _parse_price(cells[4].get_text(strip=True))

            elif "ทองรูปพรรณ" in text and len(cells) >= 5:
                prices["gold_ornament_buy"] = _parse_price(cells[2].get_text(strip=True))
                prices["gold_ornament_sell"] = _parse_price(cells[4].get_text(strip=True))

        required = {"gold_bar_buy", "gold_bar_sell", "gold_ornament_buy", "gold_ornament_sell"}
        if not required.issubset(prices.keys()):
            logger.warning("Parse ไม่ครบ — พบเพียง: %s", list(prices.keys()))
            return None

        return prices

    except Exception as e:
        logger.warning("Parse error: %s", e)
        return None


def _parse_price(text: str) -> float:
    """แปลง '45,500.00' → 45500.0"""
    return float(text.replace(",", "").strip())


def scrape() -> dict | None:
    """
    ดึงข้อมูลจาก goldtraders.or.th พร้อม retry 3 ครั้ง
    คืนค่า dict ราคาทอง หรือ None ถ้าล้มเหลว
    """
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info("Fetching %s (attempt %d/%d)", URL, attempt, RETRY_COUNT)
            response = requests.get(URL, timeout=15)
            response.raise_for_status()
            return parse_gold_prices(response.text)
        except Exception as e:
            logger.warning("Attempt %d failed: %s", attempt, e)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)

    logger.error("All %d attempts failed", RETRY_COUNT)
    return None
