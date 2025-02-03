import asyncio
import os
import sys

from solders.keypair import Keypair  # type: ignore

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from settings import settings  # noqa: E402


class SolanaTraderCreateWalletError(Exception):
    pass


async def main():
    keypair = Keypair()

    public_key = keypair.pubkey()
    keypair_json = keypair.to_json()

    print("Generated new wallet:")
    print(f"Public Key: {public_key}")
    print(f"Keypair json: {keypair_json}")

    file_name = settings.app_wallet_file_name
    if not file_name:
        raise SolanaTraderCreateWalletError

    with open(file_name, "w") as f:
        import json

        keypair_data = {
            "public_key": str(public_key),
            "keypair_json": keypair_json,
        }
        json.dump(keypair_data, f, indent=4)
    print(f"Saved in to '{file_name}'")


if __name__ == "__main__":
    asyncio.run(main())
