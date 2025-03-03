import asyncio
from base64 import b64decode
from typing import Any

import base58
from loguru import logger
from solana.exceptions import SolanaRpcException
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts, TxOpts
from solders import message
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.rpc.responses import RpcBlockhash  # type: ignore
from solders.signature import Signature  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore

from core.settings import settings
from models.token_models import Token
from schemas.wallet_schemas import WalletBalance, WalletTokenBalance


class WalletService:
    def __init__(self, rpc_url: str | None = settings.app_solana_rpc_url):
        if not rpc_url or not settings.app_solana_private_key:
            logger.critical(
                "No RPC URL or No Private Key provided. "
                "Unable to initialize WalletService."
            )
            raise ValueError("RPC URL and Private key must be provided.")

        self.rpc_url = rpc_url
        self.keypair = Keypair.from_bytes(
            base58.b58decode(settings.app_solana_private_key)
        )
        self.pub_key = self.keypair.pubkey()

    async def get_balance(self, token: Token) -> WalletBalance:
        async with AsyncClient(self.rpc_url) as client:
            wallet_balance = await client.get_balance(self.pub_key)
            logger.info(
                f"Wallet balance for {self.pub_key}: {wallet_balance.value}"
            )

            token_balance = None
            for try_num in range(1, 3):
                logger.warning(f"Try to get balance - {try_num}...")
                try:
                    await asyncio.sleep(2)
                    token_balance = (
                        await client.get_token_accounts_by_owner_json_parsed(
                            self.pub_key,
                            TokenAccountOpts(
                                mint=Pubkey.from_string(token.address),
                            ),
                        )
                    )
                    if token_balance:
                        break
                except SolanaRpcException:
                    continue

            if not token_balance or not token_balance.value:
                logger.warning(
                    f"No token accounts found for token: {token.name} "
                    f"owned by wallet: {self.pub_key}"
                )
                return WalletBalance(
                    amount=0,
                    token=WalletTokenBalance(name=token.name, amount=0),
                )

            token_data = token_balance.value[0].account.data.parsed.get(
                "info", {}
            )
            if not isinstance(token_data, dict):
                logger.critical(
                    "Expected token data to be a dictionary but got: "
                    f"{type(token_data).__name__}"
                )
                raise ValueError("Token data is not in the expected format.")

            token_amount_data = token_data.get("tokenAmount")
            if not isinstance(token_amount_data, dict):
                logger.critical(
                    "Expected token amount data to be a dictionary but got: "
                    f"{type(token_amount_data).__name__}"
                )
                raise ValueError(
                    "Token amount data is not in the expected format."
                )

            token_amount_data_value = token_amount_data.get("amount")
            if not isinstance(token_amount_data_value, (int, str)):
                logger.critical(
                    "Expected token amount to be int or str but got: "
                    f"{type(token_amount_data_value).__name__}"
                )
                raise ValueError("Token amount is not in the expected format.")

            result = WalletBalance(
                amount=wallet_balance.value,
                token=WalletTokenBalance(
                    name=token.name,
                    amount=int(token_amount_data_value),
                ),
            )
            logger.info(f"Successfully retrieved balances: {result}")

            return result

    async def get_latest_blockhash(self) -> RpcBlockhash:
        async with AsyncClient(self.rpc_url) as client:
            last_blockhash = await client.get_latest_blockhash()
            blockhash = last_blockhash.value
            logger.info(f"Latest blockhash retrieved: {blockhash}")

            return blockhash

    async def send_transaction(
        self, transaction_insctructions: dict[str, Any]
    ) -> Signature:
        instructions = transaction_insctructions.get("swapTransaction")
        if not instructions:
            logger.critical("No transaction instructions provided.")
            raise ValueError("Transaction instructions must be provided.")

        async with AsyncClient(self.rpc_url) as client:
            blockhash = await self.get_latest_blockhash()
            options = TxOpts(
                skip_preflight=False,
                last_valid_block_height=blockhash.last_valid_block_height,
            )
            transaction_bytes = VersionedTransaction.from_bytes(
                b64decode(instructions)
            )
            signature = self.keypair.sign_message(
                message.to_bytes_versioned(transaction_bytes.message)
            )
            signed_transaction = VersionedTransaction.populate(
                transaction_bytes.message, [signature]
            )

            logger.debug(f"Signed transaction: {signed_transaction}")

            result = await client.send_raw_transaction(
                bytes(signed_transaction),
                options,
            )
            result_tx_id = result.value
            logger.info(f"Transaction sent. TxID: {result_tx_id}")

            return result_tx_id
