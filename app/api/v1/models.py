from enum import Enum
import uuid

from pydantic import BaseModel, condecimal

class Operation(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationResponse(BaseModel):
    """
    Модель ответа на операцию
    """
    status: str
    balance: float


class WalletBalanceResponse(BaseModel):
    """
    Модель ответа на запрос баланса
    """
    balance: float


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