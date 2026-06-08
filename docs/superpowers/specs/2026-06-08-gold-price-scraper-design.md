# Gold Price Scraper — Design Spec

**Date:** 2026-06-08  
**Status:** Approved

## Overview

Python web scraper ที่ดึงราคาทองคำจาก `https://classic.goldtraders.or.th/default.aspx` และบันทึกลง MySQL database รองรับทั้งการรันแบบ on-demand (manual) และ scheduled อัตโนมัติทุก 5 นาที ผ่าน OS cron บน Server/VPS

---

## Architecture

### โครงสร้างไฟล์

```
gold-price/
├── scraper.py          # ตัว scrape เว็บ + parse ราคาทอง
├── database.py         # จัดการ MySQL connection + ORM model (SQLAlchemy)
├── main.py             # entry point — CLI interface
├── config.py           # อ่าน config จาก environment variables
├── requirements.txt
└── .env.example        # template สำหรับ DB credentials
```

### Data Flow

```
main.py (CLI)
    └──> scraper.py  →  ดึง HTML จาก goldtraders.or.th
              └──> parse ราคา
                      └──> database.py  →  INSERT ลง MySQL
```

### CLI Commands

```bash
python main.py scrape       # ดึงราคาและบันทึกทันที
python main.py latest       # แสดงราคาล่าสุดจาก DB
python main.py history 24h  # ดูประวัติย้อนหลัง 24 ชั่วโมง
python main.py init-db      # สร้าง table ใน DB (รันครั้งแรก)
```

### Cron Schedule (ทุก 5 นาที)

```
*/5 * * * * cd /path/to/gold-price && /usr/bin/python3 main.py scrape >> /var/log/gold-scraper.log 2>&1
```

---

## Database Schema

**Table: `gold_prices`** (MySQL)

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT AUTO_INCREMENT PK | Primary key |
| `scraped_at` | DATETIME | เวลาที่ดึงข้อมูล |
| `gold_bar_buy` | DECIMAL(10,2) | ราคาซื้อทองแท่ง (บาท) |
| `gold_bar_sell` | DECIMAL(10,2) | ราคาขายทองแท่ง (บาท) |
| `gold_ornament_buy` | DECIMAL(10,2) | ราคาซื้อทองรูปพรรณ (บาท) |
| `gold_ornament_sell` | DECIMAL(10,2) | ราคาขายทองรูปพรรณ (บาท) |
| `source_url` | VARCHAR(255) | URL ที่ดึงข้อมูลมา |

---

## Scraping Strategy

เว็บ `classic.goldtraders.or.th` เป็น ASP.NET WebForms ใช้แนวทาง:

1. `requests` + `BeautifulSoup` (primary) — เร็ว, ไม่ต้อง browser
2. ถ้า parse ไม่ได้ — log warning และ skip round นั้น (ไม่ crash)

---

## Error Handling

- **Retry:** อัตโนมัติ 3 ครั้งหากเชื่อมต่อ HTTP ไม่ได้ (backoff 5 วินาที)
- **Parse failure:** log warning แต่ไม่ raise exception — ป้องกัน cron ล้มเหลว
- **DB failure:** log error พร้อม stack trace ลงไฟล์ `scraper.log`

---

## Configuration

**Environment Variables (`.env`):**

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gold_prices
DB_USER=gold_user
DB_PASSWORD=secret
LOG_LEVEL=INFO
```

---

## Dependencies

```
requests
beautifulsoup4
SQLAlchemy
PyMySQL
python-dotenv
lxml
```

---

## Deployment

```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt

# 2. ตั้งค่า environment
cp .env.example .env
# แก้ไข credentials ใน .env

# 3. สร้าง DB table
python main.py init-db

# 4. ทดสอบ
python main.py scrape

# 5. ตั้ง cron
crontab -e
# เพิ่ม: */5 * * * * cd /path/to/gold-price && /usr/bin/python3 main.py scrape >> /var/log/gold-scraper.log 2>&1
```

## Logging

- บันทึกลงทั้ง console และไฟล์ `scraper.log`
- Format: `[2026-06-08 10:30:00] INFO: Scraped gold bar buy=45,500.00 sell=45,600.00`
