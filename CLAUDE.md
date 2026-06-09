# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python web scraper ดึงราคาทองคำจาก `https://classic.goldtraders.or.th/default.aspx` และบันทึกลง MySQL รองรับทั้ง manual และ cron schedule ทุก 5 นาที

## Commands

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# สร้าง table ใน MySQL (รันครั้งแรก)
python main.py init-db

# ดึงราคาทองและบันทึก
python main.py scrape

# ดูราคาล่าสุด
python main.py latest

# ดูประวัติย้อนหลัง (default 24 ชั่วโมง)
python main.py history 24h

# รัน tests ทั้งหมด
pytest tests/ -v

# รัน test เดี่ยว
pytest tests/test_scraper.py::test_parse_gold_prices_returns_correct_values -v
```

## Architecture

**Data Flow:** `main.py` (CLI) → `scraper.py` (HTTP + parse) → `database.py` (MySQL INSERT)

**Module Responsibilities:**
- `config.py` — โหลด env vars จาก `.env`, expose เป็น constants (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `LOG_LEVEL`, `DATABASE_URL`)
- `database.py` — SQLAlchemy ORM model (`GoldPrice`) + CRUD functions (`save_price`, `get_latest`, `get_history`, `init_db`)
- `scraper.py` — `scrape()` ดึง HTML + retry 3 ครั้ง, `parse_gold_prices()` parse ราคาจาก HTML
- `main.py` — CLI entry point, logging setup (stdout + `scraper.log`), wires modules together

## Database

**Table:** `gold_prices` (MySQL)

| Column | Type |
|--------|------|
| id | BIGINT PK AUTO_INCREMENT |
| scraped_at | DATETIME |
| gold_bar_buy | DECIMAL(10,2) |
| gold_bar_sell | DECIMAL(10,2) |
| gold_ornament_buy | DECIMAL(10,2) |
| gold_ornament_sell | DECIMAL(10,2) |
| source_url | VARCHAR(255) |

## Configuration

Copy `.env.example` → `.env` แล้วแก้ไข credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gold_prices
DB_USER=gold_user
DB_PASSWORD=your_password_here
LOG_LEVEL=INFO
```

## Scraper Notes

เว็บ `classic.goldtraders.or.th` เป็น ASP.NET WebForms — parse ด้วย BeautifulSoup โดยค้นหา row ที่มีข้อความ **"ทองคำแท่ง"** และ **"ทองรูปพรรณ"**

หาก HTML structure เว็บเปลี่ยน → แก้เฉพาะ `parse_gold_prices()` ใน `scraper.py` จุดเดียว

URL source อยู่ใน `scraper.py::URL` — `database.py` import ค่านี้เป็น `SOURCE_URL` (ห้ามซ้ำ 2 ที่)

## Cron Setup (Server)

```bash
# ดึงราคาทุก 5 นาที
*/5 * * * * cd /path/to/gold-price && /usr/bin/python3 main.py scrape >> /var/log/gold-scraper.log 2>&1
```

## Tests

10 unit tests แบ่งเป็น:
- `tests/test_config.py` (2) — env var loading + defaults
- `tests/test_database.py` (4) — ORM model + CRUD ใช้ SQLite in-memory
- `tests/test_scraper.py` (4) — parse logic + retry behavior ใช้ mock

SQLite in-memory ใช้สำหรับ test (`BigInteger` ใช้ `with_variant(Integer, "sqlite")` เพื่อ compatibility)
