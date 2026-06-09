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
