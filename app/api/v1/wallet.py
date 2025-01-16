import uuid
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, condecimal

from app.db.models import Wallet
from app.db.database import get_async_session
from app.exceptions import wallet_exceptions

wallet_router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


class Operation(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperation(BaseModel):
    """
    Операция с кошельком
    """
    operation: Operation
    amount: condecimal(gt=0)


class WalletUUIDResponse(BaseModel):
    """
    Модель кошелька
    """
    id_: uuid.UUID

    def __str__(self):
        return str(self.id_)


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


@wallet_router.post("/create_wallet", status_code=201)
async def create_wallet(session: AsyncSession = Depends(get_async_session)):
    """
    Создание кошелька
    session: Сессия БД
    :return: UUID кошелька
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

    return JSONResponse({"wallet_uuid": str(wallet_uuid)}, status.HTTP_201_CREATED)


@wallet_router.get("/{wallet_uuid}")
async def get_wallet(wallet_uuid: str, session: AsyncSession = Depends(get_async_session)):
    """
    Получение баланса кошелька
    :param session: Сессия БД
    :param wallet_uuid: UUID Кошелька
    :return: Баланс кошелька
    """
    try:
        balance = await get_wallet_balance(wallet_uuid, session)

    except wallet_exceptions.WalletNotFoundError:
        raise HTTPException(status_code=404, detail="Wallet not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse({"balance": balance}, status.HTTP_200_OK)


@wallet_router.post("/{wallet_uuid}/operation")
async def update_wallet(
        wallet_uuid: str,
        operation: WalletOperation,
        session: AsyncSession = Depends(get_async_session)
):
    """
    Обновление баланса кошелька
    :param session: Сессия БД
    :param wallet_uuid: UUID Кошелька
    :param operation: Тип операции и сумма операции
    :return: Баланс кошелька
    """
    try:
        new_balance = await wallet_operation(
            wallet_uuid,
            operation.operation,
            operation.amount,
            session)

        return JSONResponse({"status": "success", "balance": new_balance}, status.HTTP_200_OK)

    except wallet_exceptions.WalletNotFoundError:
        raise HTTPException(status_code=404, detail="Wallet not found")

    except wallet_exceptions.WalletBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
