import asyncio

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore

from constants import LAMPORTS_PER_SOL
from settings import settings


class SolenaTraderInitClientError(Exception):
    pass


async def get_keypair() -> Keypair:
    secret_json = settings.app_solana_keypair_json
    if not secret_json:
        raise SolenaTraderInitClientError
    keypair = Keypair.from_json(secret_json)

    return keypair


async def get_balance(client: AsyncClient, public_key: Pubkey) -> float:
    balance = await client.get_balance(public_key)
    balance_value = balance.value
    balance_in_sol = balance_value / LAMPORTS_PER_SOL

    return float(balance_in_sol)


async def get_address_owner(client: AsyncClient, public_key: Pubkey) -> str:
    account_info = await client.get_account_info(public_key)
    account_info_value = account_info.value

    return str(account_info_value.owner) if account_info_value else "None"


async def send_one_sol(client: AsyncClient, public_key: Pubkey):
    result = await client.request_airdrop(public_key, LAMPORTS_PER_SOL)

    if result:
        print("Success added 1 SOL")
    else:
        print(f"Add 1 SOL error: {result}")


async def main():
    keypair = await get_keypair()
    public_key = keypair.pubkey()

    async with AsyncClient(settings.app_solana_rpc_url) as client:
        balance_in_sol = await get_balance(client, public_key)
        account_owner = await get_address_owner(client, public_key)

        print(f"Info key {public_key}: {account_owner}")
        print(f"Balance: {balance_in_sol} SOL")

        if not balance_in_sol:
            await send_one_sol(client, public_key)


if __name__ == "__main__":
    asyncio.run(main())
