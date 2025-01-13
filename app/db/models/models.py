import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True


class Wallet(Base):
    """
    Модель кошелька
    """
    __tablename__ = 'wallets'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    balance: Mapped[float] = mapped_column(nullable=False, default=0.0)

    __table_args__ = (
        CheckConstraint(
            'balance >= 0',
            name='balance_check'
        ),
    )
