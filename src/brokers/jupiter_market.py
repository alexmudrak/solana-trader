from typing import Any
from urllib.parse import urljoin

import httpx
from loguru import logger

from brokers.abstract_market import AbstractMarket


class JupiterMarket(AbstractMarket):
    BASE_URL = "https://api.jup.ag"
    PRICE_PATH = "/price/v2?ids={to_tokens_string}&vsToken={from_token}"
    QUOTE_PATH = "/swap/v1/quote?inputMint={from_token}&outputMint={to_token}&amount={amount}&slippageBps={slippage}&restrictIntermediateTokens=true"
    SWAP_PATH = "/swap/v1/swap"
    TOKEN_INFO_PATH = "/tokens/v1/token/{token}"

    def __init__(self):
        self.slippage = 50

    async def get_quote_tokens(
        self, from_token: str, to_token: str, amount: float
    ) -> dict[str, Any]:
        url = urljoin(
            self.BASE_URL,
            self.QUOTE_PATH.format(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                slippage=self.slippage,
            ),
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            logger.debug(f"Received quote response: {response.json()}")

            return response.json()

    async def make_transaction(self, quote: dict, wallet_pub_key: str):
        url = urljoin(
            self.BASE_URL,
            self.SWAP_PATH,
        )
        data = {
            "quoteResponse": quote,
            "userPublicKey": wallet_pub_key,
            "wrapUnwrapSOL": True,
            "computeUnitPriceMicroLamports": 20 * 14000,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            response.raise_for_status()

            logger.debug(f"Transaction response: {response.json()}")

            return response.json()

    async def get_price(
        self,
        from_token: str,
        to_tokens: list[str],
    ) -> dict[str, Any]:
        to_tokens_string = ",".join(to_tokens)
        url = urljoin(
            self.BASE_URL,
            self.PRICE_PATH.format(
                to_tokens_string=to_tokens_string,
                from_token=from_token,
            ),
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            logger.debug(f"Received price response: {response.json()}")

            return response.json()

    async def get_token_info(
        self,
        token: str,
    ) -> dict[str, Any]:
        url = urljoin(
            self.BASE_URL,
            self.TOKEN_INFO_PATH.format(token=token),
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            logger.debug(f"Received token info response: {response.json()}")

            return response.json()
