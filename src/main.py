import asyncio

from solana.rpc.async_api import AsyncClient
from solders.hash import Hash  # type: ignore
from solders.instruction import Instruction  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solders.message import MessageV0  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.rpc.responses import SendTransactionResp  # type: ignore
from solders.system_program import TransferParams, transfer
from solders.transaction import (  # type: ignore
    VersionedTransaction,
)

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


async def make_instruction(
    public_key: Pubkey,
    recipient_hash: Pubkey,
    count: int,
) -> Instruction:
    instruction = transfer(
        TransferParams(
            from_pubkey=public_key,
            to_pubkey=recipient_hash,
            lamports=count,
        )
    )

    return instruction


async def get_latest_blockhash(client: AsyncClient) -> Hash:
    last_blockhash = await client.get_latest_blockhash()
    blockhash = last_blockhash.value.blockhash

    return blockhash


async def send_transaction(
    client: AsyncClient,
    keypair: Keypair,
    recipient_public_key: Pubkey,
    count: int,
) -> SendTransactionResp:
    sender_public_key = keypair.pubkey()

    instruction = await make_instruction(
        sender_public_key,
        recipient_public_key,
        count,
    )
    blockhash = await get_latest_blockhash(client)

    message = MessageV0.try_compile(
        payer=sender_public_key,
        instructions=[instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash,
    )

    transaction = VersionedTransaction(message, [keypair])

    print(f"Sending transaction to {recipient_public_key}: {count} lamports")
    result = await client.send_transaction(transaction)

    return result


async def main():
    keypair = await get_keypair()
    public_key = keypair.pubkey()

    recipient_address = Keypair()
    recipient_public_key = recipient_address.pubkey()
    print(f"Recipient address: {recipient_public_key}")

    async with AsyncClient(settings.app_solana_rpc_url) as client:
        balance_in_sol = asyncio.create_task(get_balance(client, public_key))
        account_owner = asyncio.create_task(
            get_address_owner(client, public_key)
        )

        balance_in_sol, account_owner = await asyncio.gather(
            balance_in_sol, account_owner
        )
        print(f"Info key {public_key}: {account_owner}")
        print(f"Balance: {balance_in_sol} SOL")

        if not balance_in_sol:
            await send_one_sol(client, public_key)
            await asyncio.sleep(5)

        transaction_result = await send_transaction(
            client,
            keypair,
            recipient_public_key,
            1_000_000,
        )

        print(f"Transaction result: {transaction_result.value}")
        await asyncio.sleep(20)

        balance_in_sol = await get_balance(client, public_key)
        print(f"Balance: {balance_in_sol} SOL")


if __name__ == "__main__":
    asyncio.run(main())
