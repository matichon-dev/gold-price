from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from scraper import URL as SOURCE_URL

TZ_BANGKOK = ZoneInfo("Asia/Bangkok")


class Base(DeclarativeBase):
    pass


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
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
        scraped_at=datetime.now(TZ_BANGKOK),
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
    since = datetime.now(TZ_BANGKOK) - timedelta(hours=hours)
    return (
        session.query(GoldPrice)
        .filter(GoldPrice.scraped_at >= since)
        .order_by(GoldPrice.scraped_at.desc())
        .all()
    )
