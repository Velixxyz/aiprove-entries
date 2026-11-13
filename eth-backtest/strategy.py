#!/usr/bin/env python3
"""ETH 1-minute mean-reversion strategy for the AIProve eth-pnl-fixed bounty.

Rule: RSI(14) fade. Long 1 unit when RSI < 25, short 1 unit when RSI > 75,
flat when RSI returns to 45-55. No lookahead: the signal at bar t uses closes
up to t and the position applies from bar t+1's open.

Why this rule: 1-minute bars are noise-dominated, so fading short-term
extremes beats trend-following here; among a small set of standard rules
tested (EMA crossovers, Bollinger fades, Donchian breakouts, RSI fades) this
one was picked for robustness -- few trades (low cost drag) and the lowest
max drawdown -- not for the highest in-sample PnL.

Costs (stated assumptions; the sandbox applies its own costing on replay):
taker fee 0.05% + slippage 0.01% per fill.

Usage: python3 strategy.py [bars.csv] -> prints positions + PnL report.
"""
import csv, sys

def rsi(closes, n=14):
    gains, losses = [0.0]*len(closes), [0.0]*len(closes)
    for i in range(1, len(closes)):
        d = closes[i]-closes[i-1]
        gains[i], losses[i] = max(d, 0), max(-d, 0)
    out = [50.0]*len(closes)
    ag = sum(gains[1:n+1])/n; al = sum(losses[1:n+1])/n
    for i in range(n, len(closes)):
        ag = (ag*(n-1)+gains[i])/n; al = (al*(n-1)+losses[i])/n
        out[i] = 100-100/(1+ag/al) if al > 0 else 100.0
    return out

def backtest(path, fee=0.0005, slip=0.0001):
    rows = list(csv.DictReader(open(path)))
    closes = [float(r["close"]) for r in rows]
    opens = [float(r["open"]) for r in rows]
    R = rsi(closes)
    sig, cur = [0]*len(closes), 0
    for i in range(len(closes)):
        if R[i] < 25: cur = 1
        elif R[i] > 75: cur = -1
        elif 45 <= R[i] <= 55: cur = 0
        sig[i] = cur
    pos, entry, pnl, trades, peak, maxdd = 0, 0.0, 0.0, 0, 0.0, 0.0
    for t in range(1, len(rows)):
        px = opens[t]
        if sig[t-1] != pos:
            if pos: pnl += pos*(px-entry)-(fee+slip)*px; trades += 1
            if sig[t-1]: pos, entry = sig[t-1], px; pnl -= (fee+slip)*px; trades += 1
            else: pos = 0
        eq = pnl + (pos*(closes[t]-entry) if pos else 0)
        peak = max(peak, eq); maxdd = max(maxdd, peak-eq)
    if pos: pnl += pos*(closes[-1]-entry)-(fee+slip)*closes[-1]
    return {"net_pnl_usd_per_unit": round(pnl, 2), "trades": trades,
            "max_drawdown_usd": round(maxdd, 2), "bars": len(rows),
            "final_position": pos}

if __name__ == "__main__":
    print("ETH-backtest report:", backtest(sys.argv[1] if len(sys.argv) > 1 else "bars.csv"))
