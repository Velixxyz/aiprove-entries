# eth-pnl-fixed
Mean-reversion strategy on the frozen ETH 1-minute dataset (1,440 Binance
ETH/USDT bars, 24h ending 2026-11-13 12:17 UTC, copied here as `bars.csv`
with attribution to the challenge repo).

Rule: RSI(14) fade — long under 25, short over 75, flat at 45-55. No
lookahead (signal from closes up to bar t, position from bar t+1 open).
Costs in the local replay: 0.05% taker fee + 0.01% slippage per fill.

Run: `python3 strategy.py` — prints net PnL per unit, trade count, max drawdown.
