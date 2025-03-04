from loguru import logger

from brokers.abstract_market import AbstractMarket
from core.constants import MARKET_FEE
from models.token_models import Token
from schemas.transaction_schemas import TransactionResult
from services.wallet_service import WalletService


class TransactionService:
    def __init__(
        self,
        wallet_service: WalletService,
        market_service: AbstractMarket,
    ):
        self.wallet = wallet_service
        self.market_service = market_service
        self.market_fee = MARKET_FEE

    async def buy(
        self,
        from_token: Token,
        to_token: Token,
        buy_amount: float,
        last_market_price: float,
    ) -> TransactionResult | None:
        buy_market_price_with_fee = last_market_price * self.market_fee
        expect_buy_price = buy_market_price_with_fee * buy_amount
        receive_token_amount = int(to_token.decimals * buy_amount)
        required_token_amount = int(
            buy_market_price_with_fee * from_token.decimals * buy_amount
        )

        # Make BUY swap transaction
        dex_quote = await self.market_service.get_quote_tokens(
            from_token.address,
            to_token.address,
            required_token_amount,
        )

        dex_receive_amount = int(dex_quote["outAmount"])
        dex_send_amount = int(dex_quote["inAmount"])
        dex_swap_value = float(dex_quote["swapUsdValue"])

        if dex_receive_amount < receive_token_amount:
            logger.critical(
                "Received amount from DEX is less than expected. "
                f"Get: {dex_receive_amount} expect: {receive_token_amount}"
            )
            return

        if dex_swap_value > expect_buy_price:
            logger.critical("Spend more than expected")
            return

        dex_transaction_instructions = (
            await self.market_service.make_transaction(
                dex_quote, str(self.wallet.pub_key)
            )
        )

        # Check wallet balance
        base_token_balance = await self.wallet.get_balance(from_token)
        if (
            not base_token_balance.token
            or required_token_amount > base_token_balance.token.amount
        ):
            logger.warning(
                "Insufficient balance for buying. "
                f"Required: {required_token_amount}, "
                f"Available: {base_token_balance.token.amount if base_token_balance.token else 0}"
            )
            return

        # Send transaction
        await self.wallet.send_transaction(dex_transaction_instructions)

        return TransactionResult(
            send_amount=dex_send_amount,
            receive_amount=dex_receive_amount,
            price=buy_market_price_with_fee,
        )

    async def sell(
        self,
        from_token: Token,
        to_token: Token,
        sell_token_amount: int,
        last_market_price: float,
        take_profit_price: float = 0.0,
    ):
        sell_market_price_with_fee = last_market_price / self.market_fee
        receive_token_amount = int(take_profit_price * to_token.decimals)
        # Make BUY swap transaction
        dex_quote = await self.market_service.get_quote_tokens(
            from_token.address,
            to_token.address,
            sell_token_amount,
        )

        dex_transaction_instructions = (
            await self.market_service.make_transaction(
                dex_quote, str(self.wallet.pub_key)
            )
        )

        dex_receive_amount = int(dex_quote["outAmount"])
        dex_send_amount = int(dex_quote["inAmount"])
        dex_swap_value = float(dex_quote["swapUsdValue"])

        if dex_receive_amount < receive_token_amount:
            logger.critical(
                "Received amount from DEX is less than expected. "
                f"Get: {dex_receive_amount} expect: {receive_token_amount}"
            )
            return

        if take_profit_price and dex_swap_value < take_profit_price:
            logger.critical("Get less than expected")
            return

        # Check wallet balance
        base_token_balance = await self.wallet.get_balance(to_token)
        if (
            not base_token_balance.token
            or sell_token_amount > base_token_balance.amount
        ):
            logger.warning(
                "Insufficient balance for selling. "
                f"Required: {sell_token_amount}, "
                f"Available: {base_token_balance.amount if base_token_balance.token else 0}"
            )
            return

        # Send transaction
        await self.wallet.send_transaction(dex_transaction_instructions)

        return TransactionResult(
            send_amount=dex_send_amount,
            receive_amount=dex_receive_amount,
            price=sell_market_price_with_fee,
        )
