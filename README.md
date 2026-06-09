# Gold Price Scraper

ดึงราคาทองคำจาก [สมาคมค้าทองคำ (GTA)](https://classic.goldtraders.or.th/default.aspx) และบันทึกลง MySQL รองรับการรันแบบ manual และ scheduled ทุก 5 นาทีผ่าน cron

## ข้อมูลที่เก็บ

| ข้อมูล | คำอธิบาย |
|--------|----------|
| ราคาซื้อ/ขาย ทองคำแท่ง 96.5% | บาทละ |
| ราคาซื้อ/ขาย ทองรูปพรรณ 96.5% | บาทละ |
| เวลาที่ดึงข้อมูล | timestamp |

## Requirements

- Python 3.8+
- MySQL 5.7+ หรือ MariaDB 10.3+

## การติดตั้ง

```bash
# 1. clone โปรเจค
git clone <repo-url>
cd gold-price

# 2. สร้าง virtual environment (แนะนำ โดยเฉพาะบน Debian/Ubuntu)
python3 -m venv venv
source venv/bin/activate

# 3. ติดตั้ง dependencies
pip install -r requirements.txt

# 4. ตั้งค่า environment
cp .env.example .env
```

แก้ไข `.env` ให้ตรงกับ MySQL ของคุณ:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gold_prices
DB_USER=your_user
DB_PASSWORD=your_password
LOG_LEVEL=INFO
API_KEY=your_api_key_here
```

```bash
# 5. สร้าง database ใน MySQL
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS gold_prices CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. สร้าง table
python main.py init-db
```

> **หมายเหตุ:** ทุกครั้งที่ login เข้า server ต้อง activate venv ก่อน:
> ```bash
> source venv/bin/activate
> ```

## การใช้งาน

```bash
# ดึงราคาทองและบันทึกลง DB
python main.py scrape

# ดูราคาล่าสุด
python main.py latest

# ดูประวัติย้อนหลัง 24 ชั่วโมง
python main.py history 24h

# ดูประวัติย้อนหลัง 48 ชั่วโมง
python main.py history 48
```

## ตั้งค่า Cron (ทุก 5 นาที)

```bash
crontab -e
```

เพิ่ม (ใช้ python จาก venv):
```
*/5 * * * * cd /path/to/gold-price && /path/to/gold-price/venv/bin/python main.py scrape >> /var/log/gold-scraper.log 2>&1
```

## Gold Price API

รัน REST API สำหรับให้เว็บอื่นดึงราคาทองล่าสุด:

```bash
# Development
venv/bin/uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Production
venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
```

**Endpoint:**

```
GET /api/latest
Header: X-API-Key: <your_api_key>
```

ตัวอย่าง response:
```json
{
  "scraped_at": "2026-06-09 10:30:00",
  "gold_bar_buy": 45500.00,
  "gold_bar_sell": 45600.00,
  "gold_ornament_buy": 44850.00,
  "gold_ornament_sell": 46100.00,
  "source_url": "https://classic.goldtraders.or.th/default.aspx"
}
```

ดู interactive docs ได้ที่ `http://your-server:8000/docs`

## โครงสร้างโปรเจค

```
gold-price/
├── main.py          # CLI entry point
├── api.py           # FastAPI REST API
├── scraper.py       # ดึงและ parse ราคาจากเว็บ
├── database.py      # SQLAlchemy model + CRUD
├── config.py        # โหลด environment variables
├── requirements.txt
├── .env.example
└── tests/
    ├── test_config.py
    ├── test_database.py
    ├── test_scraper.py
    └── test_api.py
```

## การรัน Tests

```bash
pytest tests/ -v
```

## Logs

- **Console** — แสดง real-time ขณะรัน
- **scraper.log** — บันทึกทุก session (ไม่ถูก commit ใน git)
