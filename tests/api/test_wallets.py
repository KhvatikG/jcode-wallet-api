import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_wallet(test_client):
    """Тест создания нового кошелька"""
    response = await test_client.post("/api/v1/wallets/create_wallet")
    assert response.status_code == 201

    data = response.json()
    assert "wallet_uuid" in data


async def test_get_wallet_balance(test_client):
    """Тест получения баланса кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Получаем баланс
    response = await test_client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert response.status_code == 200

    data = response.json()
    assert "balance" in data
    assert data["balance"] == 0


async def test_get_nonexistent_wallet(test_client):
    """Тест получения несуществующего кошелька"""
    response = await test_client.get("/api/v1/wallets/nonexistent-uuid")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


async def test_wallet_deposit(test_client):
    """Тест пополнения кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
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


async def test_wallet_withdraw(test_client):
    """Тест снятия средств с кошелька"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Сначала пополняем
    await test_client.post(
        f"/api/v1/wallets/{wallet_uuid}/operation",
        json={"operation": "DEPOSIT", "amount": "100.00"}
    )

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


async def test_wallet_withdraw_insufficient_funds(test_client):
    """Тест снятия средств при недостаточном балансе"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
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
    assert response.json()["detail"] == "Wallet balance error"


async def test_wallet_operation_invalid_amount(test_client):
    """Тест операции с недопустимой суммой"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
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


async def test_concurrent_operations(test_client):
    """Тест параллельных операций с кошельком"""
    # Создаем кошелек
    create_response = await test_client.post("/api/v1/wallets/create_wallet")
    wallet_uuid = create_response.json()["wallet_uuid"]

    # Выполняем несколько депозитов параллельно
    import asyncio
    deposit_data = {
        "operation": "DEPOSIT",
        "amount": "10.00"
    }

    async def make_deposit():
        return await test_client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json=deposit_data
        )

    # Делаем 5 параллельных депозитов
    responses = await asyncio.gather(*[make_deposit() for _ in range(5)])

    # Проверяем, что все операции успешны
    assert all(r.status_code == 200 for r in responses)

    # Проверяем финальный баланс
    balance_response = await test_client.get(f"/api/v1/wallets/{wallet_uuid}")
    final_balance = float(balance_response.json()["balance"])
    assert final_balance == 50.00  # 5 * 10.00
