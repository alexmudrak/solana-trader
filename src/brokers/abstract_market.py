from abc import ABC, abstractmethod
from typing import Any


class AbstractMarket(ABC):
    @abstractmethod
    async def get_quote_tokens(
        self,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_price(
        self,
        from_token: str,
        to_tokens: list[str],
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def make_transaction(
        self,
        quote: dict,
        wallet_pub_key: str,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_token_info(
        self,
        token: str,
    ) -> dict[str, Any]:
        pass
