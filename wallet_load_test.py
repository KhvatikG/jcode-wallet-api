from locust import HttpUser, task, between
from decimal import Decimal
import random


class WalletUser(HttpUser):
    wait_time = between(0.001, 0.002)  # Чтобы достичь ~1000 RPS
    wallet_id = None

    def on_start(self):
        # Создаем кошелек при старте пользователя
        response = self.client.post("/api/v1/wallets/create_wallet")
        if response.status_code == 201:
            self.wallet_id = response.json()["wallet_uuid"]
            # Сделаем начальный депозит для возможности тестирования снятия
            self.client.post(
                f"/api/v1/wallets/{self.wallet_id}/operation",
                json={"operation": "DEPOSIT", "amount": "1000000"}
            )

    @task(40)
    def check_balance(self):
        if self.wallet_id:
            self.client.get(f"/api/v1/wallets/{self.wallet_id}")

    @task(30)
    def deposit(self):
        if self.wallet_id:
            amount = random.uniform(1, 1000)
            self.client.post(
                f"/api/v1/wallets/{self.wallet_id}/operation",
                json={
                    "operation": "DEPOSIT",
                    "amount": str(Decimal(amount).quantize(Decimal("0.01")))
                }
            )

    @task(30)
    def withdraw(self):
        if self.wallet_id:
            amount = random.uniform(1, 100)
            self.client.post(
                f"/api/v1/wallets/{self.wallet_id}/operation",
                json={
                    "operation": "WITHDRAW",
                    "amount": str(Decimal(amount).quantize(Decimal("0.01")))
                }
            )
