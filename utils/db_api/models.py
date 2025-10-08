from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from data.constants import PROJECT_SHORT_NAME
from data.settings import Settings


class Base(DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    private_key: Mapped[str] = mapped_column(unique=True, index=True)
    address: Mapped[str] = mapped_column(unique=True)
    proxy_status: Mapped[str] = mapped_column(default="OK", nullable=True)
    proxy: Mapped[str] = mapped_column(default=None, nullable=True)
    galxe_account_banned: Mapped[bool] = mapped_column(default=False)
    twitter_token: Mapped[str] = mapped_column(default=None, nullable=True)
    twitter_status: Mapped[str] = mapped_column(default="OK", nullable=True)
    twitter_follow_count: Mapped[int] = mapped_column(default=0, nullable=False)
    twitter_creation_at: Mapped[datetime | None] = mapped_column(default=None)
    points: Mapped[int] = mapped_column(nullable=True, default=None)
    rank: Mapped[int] = mapped_column(nullable=True, default=None)
    pioner_galxe_completed: Mapped[bool] = mapped_column(default=False)
    completed: Mapped[bool] = mapped_column(default=False)
    first_quest_invite: Mapped[str] = mapped_column(default=None, nullable=True)
    second_quest_invite: Mapped[str] = mapped_column(default=None, nullable=True)
    third_quest_invite: Mapped[str] = mapped_column(default=None, nullable=True)

    def __repr__(self):
        if Settings().show_wallet_address_logs:
            return f"[{PROJECT_SHORT_NAME} | {self.id} | {self.address}]"
        return f"[{PROJECT_SHORT_NAME} | {self.id}]"
