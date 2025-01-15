from locust import HttpUser, task, between, events
from decimal import Decimal
import random
import requests

wallet_id = None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global wallet_id
    if wallet_id is None:
        # Используем requests для создания общего кошелька
        base_url = environment.host
        create_wallet_url = f"{base_url}/api/v1/wallets/create_wallet"
        response = requests.post(create_wallet_url)
        if response.status_code == 201:
            wallet_id = response.json()["wallet_uuid"]
            print(f"Инициализирован общий кошелек с ID: {wallet_id}")
            # Пополняем баланс кошелька
            deposit_url = f"{base_url}/api/v1/wallets/{wallet_id}/operation"
            deposit_response = requests.post(
                deposit_url,
                json={"operation": "DEPOSIT", "amount": "1000000"}
            )
            if deposit_response.status_code == 200:
                print("Общий кошелек инициализирован сufficient balance.")
            else:
                print("Не удалось инициализировать баланс общего кошелька.")
        else:
            print("Не удалось создать общий кошелек.")
            wallet_id = None


class SingleWalletUser(HttpUser):
    wait_time = between(0.001, 0.001)  # Настройка для достижения ~1000 RPS

    @task(40)
    def check_balance(self):
        if wallet_id:
            self.client.get(f"/api/v1/wallets/{wallet_id}")

    @task(30)
    def deposit(self):
        if wallet_id:
            amount = random.uniform(1, 1000)
            self.client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation": "DEPOSIT",
                    "amount": str(Decimal(amount).quantize(Decimal("0.01"))),
                }
            )

    @task(30)
    def withdraw(self):
        if wallet_id:
            amount = random.uniform(1, 100)
            self.client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={
                    "operation": "WITHDRAW",
                    "amount": str(Decimal(amount).quantize(Decimal("0.01"))),
                }
            )
