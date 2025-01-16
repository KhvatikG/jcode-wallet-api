from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import crud_services
from app.api.v1.models import WalletOperation, OperationResponse, WalletBalanceResponse
from app.db.database import get_async_session
from app.exceptions import wallet_exceptions

wallet_router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@wallet_router.post("/create_wallet", status_code=201)
async def create_wallet(session: AsyncSession = Depends(get_async_session)):
    """
    Создание кошелька
    session: Сессия БД
    :return: UUID кошелька
    """
    wallet_uuid = await crud_services.create_wallet(session)

    return JSONResponse({"wallet_uuid": str(wallet_uuid)}, status.HTTP_201_CREATED)


@wallet_router.get("/{wallet_uuid}", response_model=WalletBalanceResponse)
async def get_wallet(wallet_uuid: str, session: AsyncSession = Depends(get_async_session)):
    """
    Получение баланса кошелька
    :param session: Сессия БД
    :param wallet_uuid: UUID Кошелька
    :return: Баланс кошелька
    """
    try:
        balance = await crud_services.get_wallet_balance(wallet_uuid, session)

    except wallet_exceptions.WalletNotFoundError:
        raise HTTPException(status_code=404, detail="Wallet not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse({"balance": balance}, status.HTTP_200_OK)


@wallet_router.post("/{wallet_uuid}/operation", response_model=OperationResponse)
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
        new_balance = await crud_services.wallet_operation(
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
