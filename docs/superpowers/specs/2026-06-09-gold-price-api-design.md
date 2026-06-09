# Gold Price API — Design Spec

**Date:** 2026-06-09
**Status:** Approved

## Overview

เพิ่ม REST API endpoint สำหรับให้เว็บภายนอกเรียกดูราคาทองล่าสุดในรูปแบบ JSON โดยใช้ FastAPI อ่านข้อมูลจาก MySQL ผ่าน `database.py` ที่มีอยู่แล้ว ไม่กระทบ scraper และ cron schedule เดิม

## Architecture

```
[Cron ทุก 5 นาที] → scraper.py → MySQL
[Client GET /api/latest] → api.py (FastAPI) → database.py → MySQL → JSON
```

API และ scraper รันบน server เดียวกัน ไม่มี caching layer เพราะข้อมูลอัปเดตทุก 5 นาที และ traffic ต่ำ

## Endpoint

### GET /api/latest

ดึงราคาทองล่าสุดจาก database

**Request Header:**
```
X-API-Key: <key>
```

**Response 200 OK:**
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

**Response 401 Unauthorized** — API key ผิดหรือไม่ส่งมา:
```json
{"detail": "Invalid or missing API key"}
```

**Response 404 Not Found** — ยังไม่มีข้อมูลใน database:
```json
{"detail": "No gold price data available"}
```

## Authentication

- API key เก็บใน `.env` เป็น `API_KEY=<value>`
- Client ส่งผ่าน HTTP Header: `X-API-Key`
- ตรวจสอบด้วย FastAPI `Security` dependency ทุก request
- Key ไม่ตรง → 401 ทันที ไม่ query database

## Files ที่เปลี่ยนแปลง

| File | การเปลี่ยนแปลง |
|------|----------------|
| `api.py` | ใหม่ — FastAPI app, endpoint, auth dependency |
| `config.py` | เพิ่ม `API_KEY` constant โหลดจาก env |
| `.env` | เพิ่ม `API_KEY=<value>` (ไม่ commit) |
| `.env.example` | เพิ่ม `API_KEY=your_api_key_here` |
| `requirements.txt` | เพิ่ม `fastapi` และ `uvicorn[standard]` |

## Running the API

```bash
# Development
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1
```

FastAPI จะสร้าง interactive docs อัตโนมัติที่ `http://localhost:8000/docs`

## Out of Scope

- `/api/history` endpoint
- Rate limiting
- HTTPS (จัดการที่ reverse proxy เช่น nginx)
- Multiple API keys / key management
