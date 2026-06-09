# Gold Price API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่ม FastAPI endpoint `GET /api/latest` ที่ต้องใช้ API key และคืนค่าราคาทองล่าสุดในรูปแบบ JSON

**Architecture:** FastAPI app ใน `api.py` ใหม่ อ่านข้อมูลผ่าน `database.get_latest()` ที่มีอยู่แล้ว Auth ทำผ่าน `X-API-Key` header เทียบกับ `API_KEY` ใน `.env` ไม่มี caching เพราะ traffic ต่ำและข้อมูลอัปเดตทุก 5 นาที

**Tech Stack:** FastAPI, uvicorn, python-dotenv (มีอยู่แล้ว), SQLAlchemy (มีอยู่แล้ว), pytest, httpx (สำหรับ test FastAPI)

---

## File Map

| File | สถานะ | หน้าที่ |
|------|--------|---------|
| `api.py` | สร้างใหม่ | FastAPI app, auth dependency, endpoint `/api/latest` |
| `config.py` | แก้ไข | เพิ่ม `API_KEY` constant |
| `.env.example` | แก้ไข | เพิ่ม `API_KEY=your_api_key_here` |
| `requirements.txt` | แก้ไข | เพิ่ม `fastapi`, `uvicorn[standard]`, `httpx` |
| `tests/test_api.py` | สร้างใหม่ | Tests สำหรับ endpoint และ auth |

---

## Task 1: เพิ่ม dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: เพิ่ม packages ใน requirements.txt**

แก้ไข `requirements.txt` ให้เป็น:

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.2.2
SQLAlchemy==2.0.30
PyMySQL==1.1.1
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
fastapi==0.111.0
uvicorn[standard]==0.29.0
httpx==0.27.0
```

- [ ] **Step 2: ติดตั้ง packages**

```bash
pip install -r requirements.txt
```

Expected: ติดตั้งสำเร็จ ไม่มี error

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add fastapi, uvicorn, httpx dependencies"
```

---

## Task 2: เพิ่ม API_KEY ใน config

**Files:**
- Modify: `config.py`
- Modify: `.env.example`

- [ ] **Step 1: เพิ่ม API_KEY ใน config.py**

แก้ไข `config.py` — เพิ่มบรรทัดนี้ต่อท้าย:

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
API_KEY: str = os.getenv("API_KEY", "")

DATABASE_URL: str = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
```

- [ ] **Step 2: เพิ่ม API_KEY ใน .env.example**

แก้ไข `.env.example` เพิ่มบรรทัด:

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gold_prices
DB_USER=gold_user
DB_PASSWORD=your_password_here
LOG_LEVEL=INFO
API_KEY=your_api_key_here
```

- [ ] **Step 3: เพิ่ม API_KEY ใน .env ของตัวเอง (ไม่ commit)**

เปิดไฟล์ `.env` แล้วเพิ่ม:

```
API_KEY=your-secret-key-here
```

เลือก key ที่ random พอสมควร เช่น `gold-api-2026-abc123`

- [ ] **Step 4: Commit (เฉพาะ config.py และ .env.example)**

```bash
git add config.py .env.example
git commit -m "feat: add API_KEY config"
```

---

## Task 3: สร้าง tests สำหรับ API

**Files:**
- Create: `tests/test_api.py`

- [ ] **Step 1: สร้าง tests/test_api.py**

```python
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
```

- [ ] **Step 2: รัน tests เพื่อตรวจสอบว่า fail (api.py ยังไม่มี)**

```bash
pytest tests/test_api.py -v
```

Expected: ERROR — `ModuleNotFoundError: No module named 'api'`

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_api.py
git commit -m "test: add failing tests for GET /api/latest"
```

---

## Task 4: สร้าง api.py

**Files:**
- Create: `api.py`

- [ ] **Step 1: สร้าง api.py**

```python
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

import config
from database import get_engine, get_latest

app = FastAPI(title="Gold Price API", version="1.0.0")

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not api_key or api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


@app.get("/api/latest")
def latest(api_key: str = Security(_verify_api_key)):
    engine = get_engine(config.DATABASE_URL)
    with Session(engine) as session:
        record = get_latest(session)
    if record is None:
        raise HTTPException(status_code=404, detail="No gold price data available")
    return {
        "scraped_at": record.scraped_at.strftime("%Y-%m-%d %H:%M:%S"),
        "gold_bar_buy": float(record.gold_bar_buy),
        "gold_bar_sell": float(record.gold_bar_sell),
        "gold_ornament_buy": float(record.gold_ornament_buy),
        "gold_ornament_sell": float(record.gold_ornament_sell),
        "source_url": record.source_url,
    }
```

- [ ] **Step 2: รัน tests เพื่อตรวจสอบว่าผ่าน**

```bash
pytest tests/test_api.py -v
```

Expected:
```
PASSED tests/test_api.py::test_latest_returns_200_with_valid_key
PASSED tests/test_api.py::test_latest_returns_401_with_wrong_key
PASSED tests/test_api.py::test_latest_returns_401_with_no_key
PASSED tests/test_api.py::test_latest_returns_404_when_no_data
```

- [ ] **Step 3: รัน tests ทั้งหมดเพื่อให้แน่ใจว่าไม่ทำ tests เดิมพัง**

```bash
pytest tests/ -v
```

Expected: ผ่านทุก test (10 เดิม + 4 ใหม่ = 14 tests)

- [ ] **Step 4: Commit**

```bash
git add api.py
git commit -m "feat: add GET /api/latest endpoint with API key auth"
```

---

## Task 5: Push และทดสอบ manual

- [ ] **Step 1: Push ขึ้น GitHub**

```bash
git push
```

- [ ] **Step 2: ทดสอบรัน API บนเครื่อง**

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

- [ ] **Step 3: ทดสอบ endpoint ด้วย curl**

```bash
# ทดสอบด้วย key ที่ถูกต้อง (แทน YOUR_API_KEY ด้วยค่าใน .env)
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/latest

# ทดสอบด้วย key ผิด — ต้องได้ 401
curl -H "X-API-Key: wrong" http://localhost:8000/api/latest

# ทดสอบไม่ส่ง key — ต้องได้ 401
curl http://localhost:8000/api/latest
```

Expected response แรก:
```json
{
  "scraped_at": "2026-06-09 10:30:00",
  "gold_bar_buy": 45500.0,
  "gold_bar_sell": 45600.0,
  "gold_ornament_buy": 44850.0,
  "gold_ornament_sell": 46100.0,
  "source_url": "https://classic.goldtraders.or.th/default.aspx"
}
```
