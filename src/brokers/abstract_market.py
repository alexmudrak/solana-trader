from abc import ABC, abstractmethod
from typing import Any


class AbstractMarket(ABC):
    @abstractmethod
    async def swap_tokens(
        self, from_token: str, to_token: str, amount: float
    ) -> dict[str, Any]:
        pass
