
class WalletException(Exception):
    """
    Base class for all wallet exceptions.
    """
    pass


class WalletNotFoundError(WalletException):
    """
    Raised when a wallet is not found.
    """
    def __init__(self, wallet_uuid: str, message: str | None = None):
        self.wallet_uuid = wallet_uuid
        self.message = message or f"Wallet with uuid {wallet_uuid} not found"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class WalletBalanceError(WalletException):
    """
    Raised when a wallet balance is not enough.
    """
    def __init__(self, wallet_uuid: str, message: str | None = None):
        self.wallet_uuid = wallet_uuid
        self.message = message or f"Wallet with uuid {wallet_uuid} has not enough balance"
        super().__init__(self.message)
