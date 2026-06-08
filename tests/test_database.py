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
