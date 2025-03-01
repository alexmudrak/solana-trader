from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.token_models import Token


class TokensRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tokens(self) -> list[Token]:
        stmt = select(Token)
        result = await self.session.execute(stmt)

        tokens = list(result.scalars().all())

        return tokens

    async def get_token_by_id(self, token_id: int) -> Token | None:
        stmt = select(Token).where(Token.id == token_id)
        result = await self.session.execute(stmt)

        token = result.scalars().one_or_none()

        return token

    async def create(
        self,
        name: str,
        address: str,
        decimals: int,
    ) -> Token:
        obj = Token(
            name=name,
            address=address,
            decimals=decimals,
        )
        self.session.add(obj)
        await self.session.flush()

        return obj
