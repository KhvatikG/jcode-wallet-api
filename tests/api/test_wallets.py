import pytest
from loguru import logger
from httpx import AsyncClient, Response
import asyncio

pytestmark = pytest.mark.asyncio


async def test_create_wallet(test_client: AsyncClient):
    """Тест создания нового кошелька"""
    response = await test_client.post("/api/v1/wallets/create_wallet")
    assert response.status_code == 201

    data = response.json()
    assert "wallet_uuid" in data


async def test_get_wallet_balance(test_client: AsyncClient):
    """Тест получения баланса кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Получаем баланс
    response = await test_client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert response.status_code == 200

    data = response.json()
    assert "balance" in data
    assert data["balance"] == 0


async def test_get_nonexistent_wallet(test_client: AsyncClient):
    """Тест получения несуществующего кошелька"""
    response = await test_client.get("/api/v1/wallets/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


async def test_wallet_deposit(test_client: AsyncClient):
    """Тест пополнения кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Делаем депозит
    deposit_data = {
        "operation": "DEPOSIT",
        "amount": "100.00"
    }
    response = await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json=deposit_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert float(data["balance"]) == 100.00


async def test_wallet_withdraw(test_client: AsyncClient):
    """Тест снятия средств с кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Сначала пополняем
    deposit_response = await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation": "DEPOSIT", "amount": "100.00"}
    )
    assert deposit_response.status_code == 200

    # Снимаем средства
    withdraw_data = {
        "operation": "WITHDRAW",
        "amount": "50.00"
    }
    response = await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json=withdraw_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert float(data["balance"]) == 50.00


async def test_wallet_withdraw_insufficient_funds(test_client: AsyncClient):
    """Тест снятия средств при недостаточном балансе"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Пытаемся снять средства с пустого кошелька
    withdraw_data = {
        "operation": "WITHDRAW",
        "amount": "50.00"
    }
    response = await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json=withdraw_data
    )
    assert response.status_code == 400
    assert response.json()["detail"].endswith("has not enough balance")


async def test_wallet_operation_invalid_amount(test_client: AsyncClient):
    """Тест операции с недопустимой суммой"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Пытаемся сделать операцию с отрицательной суммой
    operation_data = {
        "operation": "DEPOSIT",
        "amount": "-50.00"
    }
    response = await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json=operation_data
    )
    assert response.status_code == 422  # Validation error


async def test_concurrent_operations(test_client: AsyncClient):
    """Тест параллельных операций с кошельком"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    assert create_response.status_code == 201
    wallet_uuid = create_response.json()["wallet_uuid"]

    deposit_data = {
        "operation": "DEPOSIT",
        "amount": "10.00"
    }

    async def make_deposit():
        return await test_client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json=deposit_data
        )

    # Создаем и запускаем задачи
    tasks = [make_deposit() for _ in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Проверяем, что все операции успешны и нет исключений
    for response in responses:
        assert isinstance(response, Response), f"Got exception instead of response: {response}"
        assert response.status_code == 200

    # Проверяем финальный баланс
    balance_response = await test_client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert balance_response.status_code == 200
    final_balance = float(balance_response.json()["balance"])
    assert final_balance == 50.00  # 5 * 10.00
