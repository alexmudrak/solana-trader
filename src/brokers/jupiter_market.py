from typing import Any
from urllib.parse import urljoin

import httpx

from brokers.abstract_market import AbstractMarket


class JupiterMarket(AbstractMarket):
    BASE_URL = "https://api.jup.ag"
    PRICE_PATH = "/price/v2?ids={to_tokens_string}&vsToken={from_token}"
    SWAP_PATH = "/swap/v1/quote?inputMint={to_token}&outputMint={from_token}&amount={amount}&slippageBps={slippage}&restrictIntermediateTokens=true"

    def __init__(self):
        self.slippage = 50

    async def swap_tokens(
        self, from_token: str, to_token: str, amount: float
    ) -> dict[str, Any]:
        url = urljoin(
            self.BASE_URL,
            self.SWAP_PATH.format(
                to_token=to_token,
                from_token=from_token,
                amount=amount,
                slippage=self.slippage,
            ),
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            return response.json()

    async def get_price(
        self,
        to_tokens: list[str],
        from_token: str,
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

            return response.json()
