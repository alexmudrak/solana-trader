from abc import ABC, abstractmethod
from typing import Any


class AbstractMarket(ABC):
    @abstractmethod
    async def swap_tokens(
        self,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_price(
        self,
        to_tokens: list[str],
        from_token: str,
    ) -> dict[str, Any]:
        pass
