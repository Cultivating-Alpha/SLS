import os

print(f"Working at {os.getcwd()}")

import pandas as pd
import numpy as np
import datetime

import pandas_ta as ta

from tradeexecutor.strategy.execution_context import ExecutionMode
from tradeexecutor.visual.equity_curve import calculate_equity_curve, calculate_returns
from tradeexecutor.visual.equity_curve import visualise_equity_curve
from tradeexecutor.analysis.trade_analyser import build_trade_analysis
import logging
from tradeexecutor.analysis.advanced_metrics import (
    visualise_advanced_metrics,
    AdvancedMetricsMode,
)


from tradeexecutor.state.visualisation import PlotKind
from tradeexecutor.strategy.cycle import CycleDuration
from tradeexecutor.strategy.default_routing_options import TradeRouting
from tradeexecutor.strategy.execution_context import ExecutionContext
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.strategy.reserve_currency import ReserveCurrency
from tradeexecutor.strategy.strategy_type import StrategyType
from tradeexecutor.strategy.trading_strategy_universe import (
    load_pair_data_for_single_exchange,
    TradingStrategyUniverse,
)
from tradeexecutor.strategy.trading_strategy_universe import load_partial_data
from tradeexecutor.strategy.universe_model import UniverseOptions
from tradingstrategy.client import Client
from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.chain import ChainId
from tradeexecutor.backtest.backtest_runner import run_backtest_inline

TRADING_STRATEGY_ENGINE_VERSION = "0.2"

# What kind of strategy we are running.
# This tells we are going to use
# NOTE: this setting has currently no effect
TRADING_STRATEGY_TYPE = StrategyType.managed_positions

# We trade on Polygon
CHAIN_ID = ChainId.polygon

# How our trades are routed.
# PancakeSwap basic routing supports two way trades with BUSD
# and three way trades with BUSD-BNB hop.
TRADE_ROUTING = TradeRouting.uniswap_v3_usdc_poly

# How often the strategy performs the decide_trades cycle.
TRADING_STRATEGY_CYCLE = CycleDuration.cycle_1h

# Time bucket for our candles
CANDLE_TIME_BUCKET = TimeBucket.h1

# Candle time granularity we use to trigger stop loss checks
STOP_LOSS_TIME_BUCKET = TimeBucket.m5

# Strategy keeps its cash in USDC
RESERVE_CURRENCY = ReserveCurrency.usdc

# Which trading pair we are backtesting on
# (Might be different from the live trading pair)
# https://tradingstrategy.ai/trading-view/polygon/quickswap/eth-usdc
TRADING_PAIR = (ChainId.arbitrum, "uniswap-v3", "WBTC", "USDC", 0.0005)


def plot(state, timestamp, indicators):
    # Visualize strategy
    # See available Plotly colours here
    # https://community.plotly.com/t/plotly-colours-list/11730/3?u=miohtama
    visualisation = state.visualisation
    visualisation.plot_indicator(
        timestamp,
        "SMA Long",
        PlotKind.technical_indicator_on_price,
        indicators["sma_long"],
        colour="darkblue",
    )
    visualisation.plot_indicator(
        timestamp,
        "SMA Short",
        PlotKind.technical_indicator_on_price,
        indicators["sma_short"],
        colour="darkblue",
    )

    visualisation.plot_indicator(
        timestamp,
        "RSI",
        PlotKind.technical_indicator_detached,
        indicators["rsi"],
        colour="#003300",
    )


# ma_long = 123
# ma_short = 11
# rsi_cutt = 13
# atr_distance = 2.5

ma_long = 112
ma_short = 6
rsi_cutt = 8
atr_distance = 2

# Expected 5.28


def get_signals(candles):
    offset = -1
    close = candles["close"].iloc[offset]
    low = candles["low"].iloc[offset]

    # Calculate indicators
    sma_short = ta.sma(candles["close"], length=ma_short).iloc[offset]
    sma_long = ta.sma(candles["close"], length=ma_long).iloc[offset]
    rsi = ta.rsi(candles["close"], length=2).iloc[offset]

    # Calculate signals

    entry = close <= sma_short and close >= sma_long and rsi <= rsi_cutt
    exit = close > sma_short

    indicators = {
        "sma_short": sma_short,
        "sma_long": sma_long,
        "rsi": rsi,
    }
    return entry, exit, indicators


def calculate_size(state, close):
    cash = state.portfolio.get_current_cash()
    return cash * 0.99


def decide_trades(timestamp, universe, state, pricing_model, cycle_debug_data):
    # The pair we are trading
    trades = []

    pair = universe.pairs.get_single()

    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=ma_long
    )

    if len(candles) < ma_long:
        # Backtest starting.
        # By default get_single_pair_data() returns the candles prior to the `timestamp`,
        # the behavior can be changed with get_single_pair_data(allow_current=True).
        # At the start of the backtest, we do not have any previous candle available yet,
        # so we cannot ask the the close price.
        return trades

    current_price = candles["close"].iloc[-1]

    entry, exit, indicators = get_signals(candles)

    # Create a position manager helper class that allows us easily to create
    # opening/closing trades for different positions
    position_manager = PositionManager(timestamp, universe, state, pricing_model)

    if not position_manager.is_any_open():
        if entry:
            # print(candles.iloc[-1])
            # print(indicators)
            buy_amount = calculate_size(state, current_price)
            trades += position_manager.open_1x_long(pair, buy_amount)
            # trades += position_manager.open_1x_long(pair, buy_amount, stop_loss_pct=sl_pct)
    else:
        if exit:
            trades += position_manager.close_all()
        # elif current_price < current_sl:
        #     current_sl = np.inf
        #     trades += position_manager.close_all()

    plot(state, timestamp, indicators)

    return trades

def create_trading_universe(
    ts: datetime.datetime,
    client: Client,
    execution_context: ExecutionContext,
    universe_options: UniverseOptions,
):
    assert isinstance(
        client, Client
    ), f"Looks like we are not running on the real data. Got: {client}"

    # Download live data from the oracle
    dataset = load_pair_data_for_single_exchange(
        client,
        time_bucket=CANDLE_TIME_BUCKET,
        pair_tickers=[TRADING_PAIR],
        execution_context=execution_context,
        universe_options=universe_options,
    )

    # Convert loaded data to a trading pair universe
    universe = TradingStrategyUniverse.create_single_pair_universe(
        dataset,
        pair=TRADING_PAIR,
    )

    return universe



import os
from pathlib import Path
from tradeexecutor.strategy.pandas_trader.alternative_market_data import (
    load_pair_candles_from_parquet,
    replace_candles,
)

# trading_pair=[
#     (ChainId.arbitrum, "uniswap-v3", "WBTC", "USDC", 0.0005),
#     # (ChainId.arbitrum, "uniswap-v3", "WETH", "USDC", 0.0005),
# ],
cycle_duration = CycleDuration.cycle_1h
initial_deposit = 10_000

reserve_currency = ReserveCurrency.usdc
trade_routing = TradeRouting.uniswap_v3_usdc_poly

#
# Load trading universe with DEX data
#
client = Client.create_jupyter_client()
universe = create_trading_universe(
    datetime.datetime.utcnow(),
    client,
    ExecutionContext(mode=ExecutionMode.backtesting),
    universe_options=UniverseOptions(),
)

print(os.getcwd())

#
# Replace the DEX price feed with Binance,
#
pair = universe.get_single_pair()
new_candles, stop_loss_candles = load_pair_candles_from_parquet(
    pair,
    Path("data/binance-BTCUSDT-1h.parquet"),
    include_as_trigger_signal=True,
)
replace_candles(universe, new_candles, stop_loss_candles)

# Change strategy backtesting period
# to match Binance data
start_at = datetime.datetime(2018, 1, 2)
end_at = datetime.datetime(2023, 9, 1)
# end_at = datetime.datetime(2018, 1, 10)





state, _, debug_dump = run_backtest_inline(
    name="SLS",
    start_at=start_at,
    end_at=end_at,
    client=client,
    cycle_duration=cycle_duration,
    decide_trades=decide_trades,
    universe=universe,
    initial_deposit=initial_deposit,
    reserve_currency=reserve_currency,
    trade_routing=trade_routing,
    log_level=logging.WARNING,
)

# |%%--%%| <mPn1IrdBaa|Sdi1wC7XJL>


trade_count = len(list(state.portfolio.get_all_trades()))
print(f"Backtesting completed, backtested strategy made {trade_count} trades")

equity = calculate_equity_curve(state)
returns = calculate_returns(equity)
metrics = visualise_advanced_metrics(returns, mode=AdvancedMetricsMode.full)

returns = metrics.loc["Cumulative Return"]
dd = metrics.loc["Max Drawdown"]
# with pd.option_context("display.max_row", None):
#     display(metrics)
print("==========")
# print(f"Total return: {returns['Strategy']}")
print(f"Max Drawdown: {dd['Strategy']}")


analysis = build_trade_analysis(state.portfolio)

summary = analysis.calculate_summary_statistics()

with pd.option_context("display.max_row", None):
    display(summary.to_dataframe())

#|%%--%%| <Sdi1wC7XJL|ozbp5HGkZb>

"""Single trading pair analysis"""
import pandas as pd
from _decimal import Decimal

from tradeexecutor.state.position import TradingPosition
from tradeexecutor.state.state import State


def expand_entries_and_exits(
    state: State,
    token_quantizer=Decimal("0.000001"),
) -> pd.DataFrame:
    """Write out a table containing entries and exists of every taken position.

    - Made for single pair strategies

    - Entry and exit are usually done using the close value
      of the previous candle

    - Assume each position contains only one entry and one exit trade

    :return:
        DataFrame indexed by position entries
    """

    items = []
    idx = []

    p: TradingPosition
    for p in state.portfolio.get_all_positions():

        first_trade = p.get_first_trade()
        last_trade = p.get_last_trade()

        # Open position at the end
        if first_trade == last_trade:
            last_trade = None

        volume = sum(t.get_volume() for t in p.trades.values())
        volume_token = sum(abs(t.get_position_quantity()) for t in p.trades.values())
        fee = sum(t.lp_fees_paid or 0 for t in p.trades.values())

        idx.append(first_trade.strategy_cycle_at)
        items.append({
            "Entry mid price": first_trade.price_structure.mid_price,
            "Exit": last_trade.strategy_cycle_at if last_trade else None,
            "Exit mid price": last_trade.price_structure.mid_price if last_trade else None,
            "PnL": p.get_total_profit_usd(),
            "Vol USD": volume,
            "Vol ": volume_token.quantize(token_quantizer),
            "LP fee": fee,
        })

    df = pd.DataFrame(items, index=idx)
    df = df.fillna("")
    df = df.replace({pd.NaT: ""})
    return df

trades = expand_entries_and_exits(state)
print(trades)
# print(trades.iloc[0])
len(trades)
trades["PnL"].sum()

trades.to_parquet("ts.parquet")



# entry = 14501.05
# exit = 14859.98
# diff = exit - entry
#
# vol = initial_deposit * 0.99/ entry
# fees = entry * vol * 0.0005 + exit * vol * 0.0005
# pnl = diff * vol - fees
#
# print()
# print()
# print()
# print("Expect PNL for first trade: ", pnl)
# print("Expected fees: ",fees)
# print("Expected volume: ", vol)
