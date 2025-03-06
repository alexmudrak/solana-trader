# Solana Trader

<p align="center">
    <img width="200" src="media/logo.jpg" alt="Solana Trader Logo" />
</p>

<hr />

## Overview

This project is a trading service that allows you to trade on the Jupiter DEX
using the Solana blockchain. The main trading direction supported by this
project is from **USDC to other tokens**.

## Features

<p align="center">
    <img width="600" src="media/chart.png" alt="Trading Chart" />
</p>

<hr />

- Auto trade between USDC and various tokens on the Jupiter DEX.
- Analyze market conditions using technical indicators such as
EMA (Exponential Moving Average) and RSI (Relative Strength Index).
- Monitor open orders and perform transactions.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/alexmudrak/solana-trader
   ```

2. Navigate to the project directory:

   ```bash
   cd solana-trader
   ```

3. Copy `.env.example` to `.env` and set the required environment variables:

   **MANDATORY**
   ```bash
   # Solana Settings
   APP_SOLANA_PRIVATE_KEY=

   # Notification config
   APP_TELEGRAM_BOT=
   APP_TELEGRAM_ADMIN=
   ```

4. Run the Docker container:

   ```bash
   docker-compose up --build
   ```

5. Access the UI at:

   ```
   http://localhost:8000
   ```

## Usage

1. First, add the USDC token at `http://localhost:8000/add-token` and any
other tokens you want to trade.
2. Create and select a trading pair at `http://localhost:8000/create-pair`.
3. Set up your trading settings and check whether auto buy/sell is enabled.

## Warning

**This project is for educational purposes only.** It does not guarantee
profit from trading activities. Please do your own research and be aware of
the risks involved in trading cryptocurrencies.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Tech Stack

| Backend   | Frontend   |
|-----------|------------|
| FastAPI   | HTMX       |
| SQLite    | JavaScript  |

Enjoy trading! 😉
