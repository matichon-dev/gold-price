# Gold Price Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Python web scraper ดึงราคาทองจาก goldtraders.or.th บันทึกลง MySQL รองรับ manual + cron schedule ทุก 5 นาที

**Architecture:** CLI entry point (`main.py`) รับ command แล้วเรียก `scraper.py` ดึง HTML จาก goldtraders.or.th และ parse ราคา จากนั้นส่งผ่าน `database.py` INSERT ลง MySQL โดยใช้ SQLAlchemy ORM configuration โหลดจาก `.env` ผ่าน `config.py`

**Tech Stack:** Python 3.8+, requests, BeautifulSoup4, SQLAlchemy, PyMySQL, python-dotenv, lxml, pytest

---

## File Map

| File | สร้าง/แก้ไข | หน้าที่ |
|------|-------------|---------|
| `requirements.txt` | สร้าง | dependencies ทั้งหมด |
| `.env.example` | สร้าง | template สำหรับ credentials |
| `config.py` | สร้าง | โหลด env vars และ expose เป็น config object |
| `database.py` | สร้าง | SQLAlchemy model + session factory + CRUD |
| `scraper.py` | สร้าง | HTTP request + BeautifulSoup parse + retry logic |
| `main.py` | สร้าง | CLI interface (scrape/latest/history/init-db) |
| `tests/test_scraper.py` | สร้าง | unit tests สำหรับ parse logic |
| `tests/test_database.py` | สร้าง | unit tests สำหรับ DB model |

---

## Task 1: Project Bootstrap — requirements.txt และ .env.example

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `tests/__init__.py`

- [ ] **Step 1: สร้าง requirements.txt**

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.2.2
SQLAlchemy==2.0.30
PyMySQL==1.1.1
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
```

- [ ] **Step 2: สร้าง .env.example**

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gold_prices
DB_USER=gold_user
DB_PASSWORD=secret
LOG_LEVEL=INFO
```

- [ ] **Step 3: สร้าง tests/__init__.py (ไฟล์เปล่า)**

```python
```

- [ ] **Step 4: ติดตั้ง dependencies**

```bash
pip install -r requirements.txt
```

Expected output: Successfully installed ... (ไม่มี error)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example tests/__init__.py
git commit -m "feat: add project dependencies and env template"
```

---

## Task 2: config.py — โหลด Environment Variables

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: เขียน failing test**

สร้างไฟล์ `tests/test_config.py`:

```python
import os
import pytest
from unittest.mock import patch


def test_config_loads_db_settings():
    env = {
        "DB_HOST": "myhost",
        "DB_PORT": "3307",
        "DB_NAME": "mydb",
        "DB_USER": "myuser",
        "DB_PASSWORD": "mypass",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        assert config.DB_HOST == "myhost"
        assert config.DB_PORT == 3307
        assert config.DB_NAME == "mydb"
        assert config.DB_USER == "myuser"
        assert config.DB_PASSWORD == "mypass"
        assert config.LOG_LEVEL == "DEBUG"


def test_config_default_port():
    env = {
        "DB_HOST": "localhost",
        "DB_NAME": "gold_prices",
        "DB_USER": "root",
        "DB_PASSWORD": "pass",
    }
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        assert config.DB_PORT == 3306
        assert config.LOG_LEVEL == "INFO"
```

- [ ] **Step 2: รัน test ให้ fail ก่อน**

```bash
pytest tests/test_config.py -v
```

Expected: FAILED (ModuleNotFoundError: No module named 'config')

- [ ] **Step 3: สร้าง config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
DB_NAME: str = os.getenv("DB_NAME", "gold_prices")
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

DATABASE_URL: str = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
```

- [ ] **Step 4: รัน test ให้ผ่าน**

```bash
pytest tests/test_config.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config loader from environment variables"
```

---

## Task 3: database.py — SQLAlchemy Model และ CRUD

**Files:**
- Create: `database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: เขียน failing tests**

สร้างไฟล์ `tests/test_database.py`:

```python
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import Base, GoldPrice, save_price, get_latest, get_history


@pytest.fixture
def db_session():
    """ใช้ SQLite in-memory สำหรับ test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_gold_price_model_has_correct_columns(db_session):
    price = GoldPrice(
        scraped_at=datetime(2026, 6, 8, 10, 0, 0),
        gold_bar_buy=45500.00,
        gold_bar_sell=45600.00,
        gold_ornament_buy=44650.00,
        gold_ornament_sell=45950.00,
        source_url="https://classic.goldtraders.or.th/default.aspx",
    )
    db_session.add(price)
    db_session.commit()
    assert price.id is not None
    assert price.gold_bar_buy == 45500.00


def test_save_price_inserts_record(db_session):
    data = {
        "gold_bar_buy": 45500.00,
        "gold_bar_sell": 45600.00,
        "gold_ornament_buy": 44650.00,
        "gold_ornament_sell": 45950.00,
    }
    save_price(db_session, data)
    result = db_session.query(GoldPrice).first()
    assert result is not None
    assert result.gold_bar_buy == 45500.00
    assert result.source_url == "https://classic.goldtraders.or.th/default.aspx"


def test_get_latest_returns_most_recent(db_session):
    for buy in [45000.00, 45500.00, 46000.00]:
        db_session.add(GoldPrice(
            scraped_at=datetime.now(),
            gold_bar_buy=buy,
            gold_bar_sell=buy + 100,
            gold_ornament_buy=buy - 850,
            gold_ornament_sell=buy + 350,
            source_url="https://classic.goldtraders.or.th/default.aspx",
        ))
    db_session.commit()
    latest = get_latest(db_session)
    assert latest.gold_bar_buy == 46000.00


def test_get_history_returns_records_within_hours(db_session):
    from datetime import timedelta
    now = datetime.now()
    for hours_ago in [1, 12, 25]:
        db_session.add(GoldPrice(
            scraped_at=now - timedelta(hours=hours_ago),
            gold_bar_buy=45500.00,
            gold_bar_sell=45600.00,
            gold_ornament_buy=44650.00,
            gold_ornament_sell=45950.00,
            source_url="https://classic.goldtraders.or.th/default.aspx",
        ))
    db_session.commit()
    results = get_history(db_session, hours=24)
    assert len(results) == 2  # 1h และ 12h ago เท่านั้น
```

- [ ] **Step 2: รัน test ให้ fail ก่อน**

```bash
pytest tests/test_database.py -v
```

Expected: FAILED (ImportError: cannot import name 'Base' from 'database')

- [ ] **Step 3: สร้าง database.py**

```python
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

SOURCE_URL = "https://classic.goldtraders.or.th/default.aspx"


class Base(DeclarativeBase):
    pass


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    gold_bar_buy: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    gold_bar_sell: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    gold_ornament_buy: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    gold_ornament_sell: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)


def get_engine(database_url: str):
    return create_engine(database_url)


def init_db(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)


def save_price(session: Session, data: dict) -> GoldPrice:
    price = GoldPrice(
        scraped_at=datetime.now(),
        gold_bar_buy=data["gold_bar_buy"],
        gold_bar_sell=data["gold_bar_sell"],
        gold_ornament_buy=data["gold_ornament_buy"],
        gold_ornament_sell=data["gold_ornament_sell"],
        source_url=SOURCE_URL,
    )
    session.add(price)
    session.commit()
    return price


def get_latest(session: Session) -> Optional[GoldPrice]:
    return session.query(GoldPrice).order_by(GoldPrice.scraped_at.desc()).first()


def get_history(session: Session, hours: int = 24) -> list[GoldPrice]:
    since = datetime.now() - timedelta(hours=hours)
    return (
        session.query(GoldPrice)
        .filter(GoldPrice.scraped_at >= since)
        .order_by(GoldPrice.scraped_at.desc())
        .all()
    )
```

- [ ] **Step 4: รัน test ให้ผ่าน**

```bash
pytest tests/test_database.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat: add SQLAlchemy model and CRUD functions for gold_prices"
```

---

## Task 4: scraper.py — HTTP Request + Parse + Retry

**Files:**
- Create: `scraper.py`
- Create: `tests/test_scraper.py`

- [ ] **Step 1: เขียน failing tests**

สร้างไฟล์ `tests/test_scraper.py`:

```python
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
```

- [ ] **Step 2: รัน test ให้ fail ก่อน**

```bash
pytest tests/test_scraper.py -v
```

Expected: FAILED (ModuleNotFoundError: No module named 'scraper')

- [ ] **Step 3: สร้าง scraper.py**

หมายเหตุ: เว็บ goldtraders.or.th ใช้ ASP.NET — HTML จริงอาจต่างจาก SAMPLE_HTML ใน test โค้ดใน `parse_gold_prices` ให้ลอง parse จาก element ที่มีข้อความ "ทองคำแท่ง" และ "ทองรูปพรรณ" ถ้า structure ต่างออกไป ให้แก้ selector ใน `parse_gold_prices` เพียงจุดเดียว โดยไม่ต้องแตะ logic อื่น

```python
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
```

- [ ] **Step 4: รัน test ให้ผ่าน**

```bash
pytest tests/test_scraper.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add gold price scraper with retry logic and HTML parser"
```

---

## Task 5: main.py — CLI Interface และ Logging

**Files:**
- Create: `main.py`

- [ ] **Step 1: สร้าง main.py**

```python
import logging
import sys
from datetime import datetime

from sqlalchemy.orm import Session

import config
import scraper
from database import get_engine, get_history, get_latest, init_db, save_price

# ── Logging setup ────────────────────────────────────────────────────────────
log_format = "[%(asctime)s] %(levelname)s: %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

ENGINE = get_engine(config.DATABASE_URL)


def cmd_init_db():
    """สร้าง table ใน MySQL"""
    init_db(config.DATABASE_URL)
    logger.info("Database initialized — table 'gold_prices' ready")


def cmd_scrape():
    """ดึงราคาทองและบันทึกลง DB"""
    logger.info("Starting scrape...")
    data = scraper.scrape()
    if data is None:
        logger.error("Scrape failed — no data saved")
        sys.exit(1)

    with Session(ENGINE) as session:
        record = save_price(session, data)

    logger.info(
        "Saved — bar buy=%.2f sell=%.2f | ornament buy=%.2f sell=%.2f",
        data["gold_bar_buy"],
        data["gold_bar_sell"],
        data["gold_ornament_buy"],
        data["gold_ornament_sell"],
    )


def cmd_latest():
    """แสดงราคาล่าสุดจาก DB"""
    with Session(ENGINE) as session:
        record = get_latest(session)

    if record is None:
        print("ยังไม่มีข้อมูลในฐานข้อมูล")
        return

    print(f"ราคาทองล่าสุด ({record.scraped_at.strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"  ทองแท่ง    ซื้อ: {record.gold_bar_buy:,.2f}  ขาย: {record.gold_bar_sell:,.2f}")
    print(f"  ทองรูปพรรณ ซื้อ: {record.gold_ornament_buy:,.2f}  ขาย: {record.gold_ornament_sell:,.2f}")


def cmd_history(hours: int = 24):
    """แสดงประวัติราคาทองย้อนหลัง N ชั่วโมง"""
    with Session(ENGINE) as session:
        records = get_history(session, hours=hours)

    if not records:
        print(f"ไม่มีข้อมูลใน {hours} ชั่วโมงที่ผ่านมา")
        return

    print(f"ประวัติราคาทอง {hours} ชั่วโมงล่าสุด ({len(records)} รายการ)")
    print(f"{'เวลา':<22} {'แท่งซื้อ':>12} {'แท่งขาย':>12} {'พรรณซื้อ':>12} {'พรรณขาย':>12}")
    print("-" * 72)
    for r in records:
        print(
            f"{r.scraped_at.strftime('%Y-%m-%d %H:%M:%S'):<22}"
            f"{r.gold_bar_buy:>12,.2f}"
            f"{r.gold_bar_sell:>12,.2f}"
            f"{r.gold_ornament_buy:>12,.2f}"
            f"{r.gold_ornament_sell:>12,.2f}"
        )


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python main.py <command>")
        print("Commands:")
        print("  init-db          สร้าง table ใน database")
        print("  scrape           ดึงราคาทองและบันทึกลง DB")
        print("  latest           แสดงราคาล่าสุด")
        print("  history [hours]  แสดงประวัติ (default: 24 ชั่วโมง)")
        sys.exit(0)

    command = args[0]

    if command == "init-db":
        cmd_init_db()
    elif command == "scrape":
        cmd_scrape()
    elif command == "latest":
        cmd_latest()
    elif command == "history":
        hours = int(args[1].replace("h", "")) if len(args) > 1 else 24
        cmd_history(hours)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: ทดสอบ help output**

```bash
python main.py
```

Expected output:
```
Usage: python main.py <command>
Commands:
  init-db          สร้าง table ใน database
  scrape           ดึงราคาทองและบันทึกลง DB
  latest           แสดงราคาล่าสุด
  history [hours]  แสดงประวัติ (default: 24 ชั่วโมง)
```

- [ ] **Step 3: รัน test ทั้งหมดให้ผ่าน**

```bash
pytest tests/ -v
```

Expected: 10 passed (ทุก test ผ่าน)

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add CLI interface with scrape/latest/history/init-db commands"
```

---

## Task 6: Integration — ทดสอบกับ MySQL จริงและตั้ง Cron

**Files:**
- Create: `.env` (จาก `.env.example`, ไม่ commit)
- Modify: `.gitignore` (สร้างใหม่)

- [ ] **Step 1: สร้าง .gitignore**

```
.env
scraper.log
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 2: ตั้งค่า .env และสร้าง DB**

```bash
cp .env.example .env
# แก้ไข .env ใส่ credentials จริง

# สร้าง database ใน MySQL ก่อน
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS gold_prices CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p -e "CREATE USER IF NOT EXISTS 'gold_user'@'localhost' IDENTIFIED BY 'secret';"
mysql -u root -p -e "GRANT ALL ON gold_prices.* TO 'gold_user'@'localhost';"

# สร้าง table
python main.py init-db
```

Expected: `[2026-06-08 10:00:00] INFO: Database initialized — table 'gold_prices' ready`

- [ ] **Step 3: ทดสอบ scrape ครั้งแรก**

```bash
python main.py scrape
```

Expected: `[...] INFO: Saved — bar buy=XX,XXX.XX sell=XX,XXX.XX | ornament buy=... sell=...`

หาก parse ไม่ได้ (เว็บมี structure ต่างจาก test): ให้ inspect HTML จริงก่อน:
```bash
python -c "import requests; print(requests.get('https://classic.goldtraders.or.th/default.aspx').text[:3000])"
```
แล้วแก้ selector ใน `scraper.py::parse_gold_prices` ให้ตรงกับ HTML จริง

- [ ] **Step 4: ตรวจสอบข้อมูลใน DB**

```bash
python main.py latest
```

Expected:
```
ราคาทองล่าสุด (2026-06-08 10:00:00)
  ทองแท่ง    ซื้อ: 45,500.00  ขาย: 45,600.00
  ทองรูปพรรณ ซื้อ: 44,650.00  ขาย: 45,950.00
```

- [ ] **Step 5: ตั้ง cron job**

```bash
# หา path ของ python3
which python3

# เปิด crontab editor
crontab -e
```

เพิ่ม line นี้ (แทนที่ `/path/to/gold-price` ด้วย path จริง):

```
*/5 * * * * cd /path/to/gold-price && /usr/bin/python3 main.py scrape >> /var/log/gold-scraper.log 2>&1
```

- [ ] **Step 6: ยืนยัน cron ทำงาน**

รอ 5-10 นาที แล้วรัน:
```bash
python main.py history 1h
```

Expected: มีข้อมูลมากกว่า 1 รายการ (แสดงว่า cron ทำงาน)

- [ ] **Step 7: Commit**

```bash
git add .gitignore
git commit -m "feat: add gitignore and complete integration setup"
```

---

## การรัน Test ทั้งหมด

```bash
pytest tests/ -v
```

Expected: 10 passed
- `test_config.py`: 2 tests
- `test_database.py`: 4 tests
- `test_scraper.py`: 4 tests
