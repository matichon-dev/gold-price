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

# 2. ติดตั้ง dependencies
pip install -r requirements.txt

# 3. ตั้งค่า environment
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
```

```bash
# 4. สร้าง database ใน MySQL
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS gold_prices CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. สร้าง table
python main.py init-db
```

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

เพิ่ม:
```
*/5 * * * * cd /path/to/gold-price && /usr/bin/python3 main.py scrape >> /var/log/gold-scraper.log 2>&1
```

## โครงสร้างโปรเจค

```
gold-price/
├── main.py          # CLI entry point
├── scraper.py       # ดึงและ parse ราคาจากเว็บ
├── database.py      # SQLAlchemy model + CRUD
├── config.py        # โหลด environment variables
├── requirements.txt
├── .env.example
└── tests/
    ├── test_config.py
    ├── test_database.py
    └── test_scraper.py
```

## การรัน Tests

```bash
pytest tests/ -v
```

## Logs

- **Console** — แสดง real-time ขณะรัน
- **scraper.log** — บันทึกทุก session (ไม่ถูก commit ใน git)
