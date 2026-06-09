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
    รองรับทั้ง structure แบบ row เดียว (เว็บจริง) และแบบ row แยก (unit tests)
    คืนค่า dict หรือ None ถ้า parse ไม่ได้
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        prices = {}

        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            texts = [c.get_text(strip=True) for c in cells]

            # จำกัด len < 50 เพื่อข้าม merged cells ที่ lxml รวม text ยาวๆ มาไว้ในเซลล์เดียว
            bar_idx = next((i for i, t in enumerate(texts) if "ทองคำแท่ง" in t and len(t) < 50), None)
            orn_idx = next((i for i, t in enumerate(texts) if "ทองรูปพรรณ" in t and len(t) < 50), None)

            if bar_idx is not None:
                bar_end = orn_idx if orn_idx is not None else len(texts)
                sell = _find_price_after_label(texts, bar_idx, bar_end, ["ขายออก", "ขาย"])
                buy = _find_price_after_label(texts, bar_idx, bar_end, ["รับซื้อ", "ซื้อ"])
                if sell is not None:
                    prices["gold_bar_sell"] = sell
                if buy is not None:
                    prices["gold_bar_buy"] = buy

                if orn_idx is not None:
                    orn_sell = _find_price_after_label(texts, orn_idx, len(texts), ["ขายออก", "ขาย"])
                    orn_buy = _find_price_after_label(texts, orn_idx, len(texts), ["รับซื้อ", "ซื้อ", "ฐานภาษี"])
                    if orn_sell is not None:
                        prices["gold_ornament_sell"] = orn_sell
                    if orn_buy is not None:
                        prices["gold_ornament_buy"] = orn_buy

            elif orn_idx is not None:
                sell = _find_price_after_label(texts, orn_idx, len(texts), ["ขายออก", "ขาย"])
                buy = _find_price_after_label(texts, orn_idx, len(texts), ["รับซื้อ", "ซื้อ", "ฐานภาษี"])
                if sell is not None:
                    prices["gold_ornament_sell"] = sell
                if buy is not None:
                    prices["gold_ornament_buy"] = buy

        # ถ้าเว็บไม่แสดง ราคารับซื้อทองรูปพรรณ ใช้ราคารับซื้อทองแท่งแทน
        if "gold_ornament_buy" not in prices and "gold_bar_buy" in prices:
            prices["gold_ornament_buy"] = prices["gold_bar_buy"]

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


def _find_price_after_label(texts: list, start: int, end: int, labels: list) -> float | None:
    """หา price ที่อยู่ถัดจาก label (ขายออก / รับซื้อ ฯลฯ) ในช่วง texts[start:end]"""
    for i in range(start, min(end, len(texts))):
        if texts[i] in labels:
            for j in range(i + 1, min(i + 3, len(texts))):
                val = texts[j].strip()
                if val:
                    try:
                        return float(val.replace(",", ""))
                    except ValueError:
                        break
    return None


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
