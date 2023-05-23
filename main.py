from threading import currentThread
import pandas as pd
from typing import List, Dict

from lib.ts_backtester import Backtester
from strategies.rsi_2.S_rsi_plot import plot

from tradeexecutor.state.trade import TradeExecution
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.state.state import State
from tradingstrategy.universe import Universe

from pandas_ta.overlap import ema, sma
from pandas_ta.momentum import rsi

# |%%--%%| <SZUpNPeecJ|0odf4siOwY>

batch_size = 200
slow_ema_candle_count = 15
fast_ema_candle_count = 5
position_size = 0.10


def calculate_indicators(universe: Universe, timestamp: pd.Timestamp):
    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=batch_size
    )

    # We have data for open, high, close, etc.
    # We only operate using candle close values in this strategy.
    close = candles["close"]

    # Calculate exponential moving averages based on slow and fast sample numbers.
    sma_short_series = sma(close, length=5)
    sma_long_series = sma(close, length=200)
    rsi_series = rsi(close, length=2)

    if sma_long_series is None or rsi_series is None:
        return None, None

    sma_long = sma_long_series.iloc[-1]
    sma_short = sma_short_series.iloc[-1]
    my_rsi = rsi_series.iloc[-1]

    return sma_short, sma_long, my_rsi


def calculate_size(state):
    # How much cash we have in the hand
    cash = state.portfolio.get_current_cash()
    return cash * position_size


def loop(
    timestamp: pd.Timestamp,
    universe: Universe,
    state: State,
    pricing_model,
    cycle_debug_data: Dict,
) -> List[TradeExecution]:
    # The pair we are trading
    pair = universe.pairs.get_single()

    sma_short, sma_long, my_rsi = calculate_indicators(universe, timestamp)
    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=batch_size
    )

    # We have data for open, high, close, etc.
    # We only operate using candle close values in this strategy.
    close = candles["close"]
    high = candles["high"]
    low = candles["low"]
    open = candles["open"]

    if sma_short is None or sma_long is None:
        # Cannot calculate EMA, because
        # not enough samples in backtesting
        return []
    current_price = close.iloc[-1]

    # List of any trades we decide on this cycle.
    # Because the strategy is simple, there can be
    # only zero (do nothing) or 1 (open or close) trades
    # decides
    trades = []

    # Create a position manager helper class that allows us easily to create
    # opening/closing trades for different positions
    position_manager = PositionManager(timestamp, universe, state, pricing_model)

    if current_price >= sma_long and current_price <= sma_short and my_rsi <= 10:
        # Entry condition:
        if not position_manager.is_any_open():
            print("====================")
            print(open.iloc[-1], high.iloc[-1], low.iloc[-1], close.iloc[-1])
            print(current_price, sma_long, sma_short)
            buy_amount = calculate_size(state)
            trades += position_manager.open_1x_long(pair, buy_amount)
    elif current_price > sma_short:
        # Exit condition:
        if position_manager.is_any_open():
            trades += position_manager.close_all()

    # plot(state, timestamp, sma, rsi)
    plot(state, timestamp, sma_long, sma_short, my_rsi)

    return trades


# |%%--%%| <0odf4siOwY|yQB6fLcUWK>

import datetime
from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.chain import ChainId

backtester = Backtester()
start_at = datetime.datetime(2021, 6, 1)
end_at = datetime.datetime(2022, 1, 1)

backtester.create_universe(
    timeframe=TimeBucket.h4,
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
)
backtester.backtest(start_at, end_at, loop)
# backtester.stats()
# |%%--%%| <yQB6fLcUWK|jxQSz2zcWR>

backtester.plot()
