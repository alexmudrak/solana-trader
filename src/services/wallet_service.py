import base58
from solana.rpc.api import Client
from solders.keypair import Keypair  # type: ignore

from core.settings import settings


class WalletService:
    def __init__(self):
        self.client = Client(settings.app_solana_rpc_url)
        self.keypair = Keypair.from_bytes(
            base58.b58decode(settings.app_solana_private_key or "")
        )
        self.pub_key = self.keypair.pubkey()

    async def get_balance(self) -> float:
        balance = self.client.get_balance(self.pub_key)
        balance_value = balance.value
        balance_in_sol = balance_value / 1_000_000
        # TODO: Add logger

        return float(balance_in_sol)
