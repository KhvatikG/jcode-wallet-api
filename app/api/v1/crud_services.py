from decimal import Decimal
from fastapi import HTTPException

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.models import Operation
from app.db.models import Wallet
from app.exceptions import wallet_exceptions


async def create_wallet(session: AsyncSession) -> str:
    """
    Создает новый кошелек в БД
    :param session: Сессия для работы с БД
    :return: id кошелька
    """
    stmt = text("""
    INSERT INTO wallets (id, balance)
        VALUES (uuid_generate_v4(), 0)
        RETURNING id
    """)
    result = await session.execute(stmt)
    wallet_uuid = result.scalar_one_or_none()

    if not wallet_uuid:
        raise HTTPException(status_code=500, detail="Failed to create wallet.")

    await session.commit()

    return wallet_uuid


async def get_wallet_balance(wallet_uuid: str, session: AsyncSession) -> int:
    stmt = select(Wallet).where(Wallet.id == wallet_uuid)
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    # Если кошелек не найден выбрасываем исключение
    if wallet is None:
        raise wallet_exceptions.WalletNotFoundError(wallet_uuid=wallet_uuid)

    return wallet.balance


async def wallet_operation(wallet_uuid: str, operation: Operation, amount: Decimal, session: AsyncSession) -> float:
    if operation == "DEPOSIT":
        stmt = text(
            """
            UPDATE wallets
            SET balance = balance + :amount
            WHERE id = :wallet_uuid
            RETURNING balance
            """
        )
    else:
        stmt = text(
            """
            UPDATE wallets
            SET balance = balance - :amount
            WHERE id = :wallet_uuid
            RETURNING balance
            """
        )

    params = {"wallet_uuid": wallet_uuid, "amount": amount}
    try:
        result = await session.execute(stmt, params)
        new_balance = result.scalar_one_or_none()

        if new_balance is None:
            raise wallet_exceptions.WalletNotFoundError(wallet_uuid=wallet_uuid)

        await session.commit()

        return new_balance

    # Если нарушено ограничение баланса, выбрасываем исключение
    except IntegrityError as e:
        if "balance_check" in str(e.orig):
            raise wallet_exceptions.WalletBalanceError(wallet_uuid=wallet_uuid)
        else:
            raise e from e