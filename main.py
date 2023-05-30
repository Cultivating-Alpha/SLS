import pandas as pd
import datetime

from lib.ts_backtester import Backtester
from strategies.rsi_2.S_rsi_plot import plot

from tradeexecutor.state.trade import TradeExecution
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.state.state import State
from tradingstrategy.universe import Universe

import pandas_ta as ta

# |%%--%%| <7p077yvyxF|yQB6fLcUWK>

from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.chain import ChainId

# Make sure that backtester is defined or not
backtester = Backtester(
    candle_time_bucket=TimeBucket.h4,
    stop_loss_time_bucket=TimeBucket.h1,
    trading_pair=[(ChainId.ethereum, "uniswap-v3", "WETH", "USDC", 0.0005)],
    start_at=datetime.datetime(2021, 1, 1),
    end_at=datetime.datetime(2023, 6, 4),
    reserve_currency="USDC",
)
# try:
#     backtester
# except NameError:
#     print("backtester is not defined")
#     backtester = Backtester(
#         timeframe=TimeBucket.h4,
#         trading_pair=("WBNB", "BUSD"),
#         chain_id=ChainId.bsc,
#         exchange_slug="pancakeswap-v2",
#     )
#     timeframe=TimeBucket.h4,
#     trading_pair=("WBNB", "BUSD"),
#     chain_id=ChainId.bsc,
#     exchange_slug="pancakeswap-v2",
# )


# |%%--%%| <yQB6fLcUWK|0odf4siOwY>

ma_long = 216
ma_short = 9
rsi_cutt = 13
atr_distance = 2

import numpy as np


def get_signals(candles):
    close = candles["close"].iloc[-1]
    low = candles["low"].iloc[-1]

    # Calculate indicators
    sma_short = ta.sma(candles["close"], length=ma_short)
    sma_short = ta.sma(candles["close"], length=ma_short).iloc[-1]
    sma_long = ta.sma(candles["close"], length=ma_long).iloc[-1]
    rsi = ta.rsi(candles["close"], length=2).iloc[-1]
    atr = ta.atr(candles["high"], candles["low"], candles["close"], length=14).iloc[-1]

    # Calculate signals
    entry = close >= sma_long and rsi <= rsi_cutt
    exit = close > sma_short
    sl = low - atr * atr_distance
    sl_pct = float(round(sl / candles["open"].iloc[-1], 2))

    indicators = {
        "sma_short": sma_short,
        "sma_long": sma_long,
        "rsi": rsi,
        "atr": atr,
    }
    return entry, exit, sl_pct, indicators


def calculate_size(state, close):
    cash = state.portfolio.get_current_cash()
    return cash * 0.99


def loop(timestamp, universe, state, pricing_model, cycle_debug_data):
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

    entry, exit, sl, indicators = get_signals(candles)

    # Create a position manager helper class that allows us easily to create
    # opening/closing trades for different positions
    position_manager = PositionManager(timestamp, universe, state, pricing_model)
    buy_amount = calculate_size(state, current_price)

    if not position_manager.is_any_open():
        if entry:
            sl = 0.98
            # trades += position_manager.open_1x_long(pair, buy_amount)
            trades += position_manager.open_1x_long(pair, buy_amount, stop_loss_pct=sl)
    else:
        if exit:
            trades += position_manager.close_all()

    plot(state, timestamp, indicators)

    return trades


start_at = datetime.datetime(2021, 9, 1)
# end_at = datetime.datetime(2021, 10, 8)
end_at = datetime.datetime(2021, 9, 7)


backtester.backtest(start_at, end_at, loop)
backtester.stats()
backtester.general_stats()
backtester.plot()

# |%%--%%| <0odf4siOwY|twF6gWbIHX>

from tradeexecutor.analysis.trade_analyser import build_trade_analysis
from IPython.core.display_functions import display

analysis = build_trade_analysis(backtester.state.portfolio)
from tradeexecutor.analysis.trade_analyser import expand_timeline

timeline = analysis.create_timeline()

expanded_timeline, apply_styles = expand_timeline(
    backtester.universe.universe.exchanges, backtester.universe.universe.pairs, timeline
)

expanded_timeline.drop(
    columns=[
        "Id",
        "Remarks",
        "Exchange",
        "Trade count",
        "Duration",
        "Base asset",
        "Quote asset",
        "PnL %",
        "PnL % raw",
    ],
    inplace=True,
)
expanded_timeline
# expanded_timeline["PnL USD"]
