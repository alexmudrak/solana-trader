import asyncio

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore

from settings import settings


class SolenaTraderInitClientError(Exception):
    pass


async def get_keypair() -> Keypair:
    secret_json = settings.app_solana_keypair_json
    if not secret_json:
        raise SolenaTraderInitClientError
    keypair = Keypair.from_json(secret_json)

    return keypair


async def main():
    keypair = await get_keypair()
    public_key = keypair.pubkey()

    async with AsyncClient(settings.app_solana_rpc_url) as client:
        response = await client.get_balance(public_key)

        print(f"Balance: {response.value}")

        response = await client.get_account_info(public_key)
        print(f"Info: {response.value}")


if __name__ == "__main__":
    asyncio.run(main())
