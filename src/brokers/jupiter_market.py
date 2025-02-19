from typing import Any

import httpx

from brokers.abstract_market import AbstractMarket


class JupiterMarket(AbstractMarket):
    BASE_URL = "https://api.jup.ag"
    PRICE_PATH = "/price/v2?ids={}&vsToken={}"

    async def swap_tokens(
        self, from_token: str, to_token: str, amount: float
    ) -> dict[str, Any]:
        return {}

    async def get_price(
        self, from_token: str, to_token: str
    ) -> dict[str, Any]:
        url = self.BASE_URL + self.PRICE_PATH.format(from_token, to_token)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            return response.json()
