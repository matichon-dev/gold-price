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


def _is_same_as_latest(session: Session, data: dict) -> bool:
    """เปรียบเทียบราคาที่ดึงมากับ record ล่าสุดใน DB — คืน True ถ้าเหมือนกัน"""
    latest = get_latest(session)
    if latest is None:
        return False
    return (
        float(latest.gold_bar_buy) == data["gold_bar_buy"]
        and float(latest.gold_bar_sell) == data["gold_bar_sell"]
        and float(latest.gold_ornament_buy) == data["gold_ornament_buy"]
        and float(latest.gold_ornament_sell) == data["gold_ornament_sell"]
    )


def cmd_scrape():
    """ดึงราคาทองและบันทึกลง DB"""
    logger.info("Starting scrape...")
    data = scraper.scrape()
    if data is None:
        logger.error("Scrape failed — no data saved")
        sys.exit(1)

    with Session(ENGINE) as session:
        if _is_same_as_latest(session, data):
            logger.info("ราคาไม่มีการเปลี่ยนแปลง — ข้ามการบันทึก")
            return
        save_price(session, data)

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
