import pandas as pd
from typing import List, Dict

from lib.ts_backtester import Backtester
from strategies.rsi_2.S_rsi_plot import plot

from tradeexecutor.state.trade import TradeExecution
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.state.state import State
from tradingstrategy.universe import Universe

from pandas_ta.overlap import ema, sma
import pandas_ta as ta

# |%%--%%| <7p077yvyxF|yQB6fLcUWK>

import datetime
from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.chain import ChainId

backtester = Backtester()

backtester.create_universe(
    timeframe=TimeBucket.h4,
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
)


# |%%--%%| <yQB6fLcUWK|0odf4siOwY>

ma_long = 216
ma_short = 9
rsi_cutt = 13
batch_size = ma_long
import talib


def calculate_indicators(candles, timestamp: pd.Timestamp):
    close = candles["close"]

    # Calculate exponential moving averages based on slow and fast sample numbers.
    sma_short_series = sma(close, length=ma_short)
    sma_long_series = sma(close, length=ma_long)
    rsi_series = ta.rsi(close, length=2)
    # rsi_series = talib.RSI(close, timeperiod=2)

    if sma_long_series is None or rsi_series is None:
        return None, None

    sma_long = sma_long_series.iloc[-1]
    sma_short = sma_short_series.iloc[-1]
    my_rsi = rsi_series.iloc[-1]

    return sma_short, sma_long, my_rsi


def calculate_size(state, close):
    # How much cash we have in the hand
    cash = state.portfolio.get_current_cash()
    return cash * 0.99
    # return cash
    return cash / close


def loop(
    timestamp: pd.Timestamp,
    universe: Universe,
    state: State,
    pricing_model,
    cycle_debug_data: Dict,
) -> List[TradeExecution]:
    # The pair we are trading
    pair = universe.pairs.get_single()
    pair.fee = 0.0050

    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=batch_size
    )

    open, high, low, close = (
        candles["open"],
        candles["high"],
        candles["low"],
        candles["close"],
    )
    # print("==========")
    # print(close)
    sma_short, sma_long, my_rsi = calculate_indicators(candles, timestamp)

    # if sma_short is None or sma_long is None:
    #     # Cannot calculate EMA, because
    #     # not enough samples in backtesting
    #     print("We have none")
    #     return []
    current_price = close.iloc[-1]
    # print(close)

    # List of any trades we decide on this cycle.
    # Because the strategy is simple, there can be
    # only zero (do nothing) or 1 (open or close) trades
    # decides
    trades = []

    # Create a position manager helper class that allows us easily to create
    # opening/closing trades for different positions
    position_manager = PositionManager(timestamp, universe, state, pricing_model)

    if current_price >= sma_long and my_rsi <= rsi_cutt:
        # Entry condition:
        if not position_manager.is_any_open():
            # print("====================")
            # print(open.tail(3))
            # print(high.tail(3))
            # print(low.tail(3))
            # print(close.tail(3))
            # print("==========")
            # print(sma_long)
            # print(sma_short)
            # print(my_rsi)
            buy_amount = calculate_size(state, current_price)
            trades += position_manager.open_1x_long(pair, buy_amount)
    elif current_price > sma_short:
        # Exit condition:
        if position_manager.is_any_open():
            trades += position_manager.close_all()

    # plot(state, timestamp, sma, rsi)
    plot(state, timestamp, sma_long, sma_short, my_rsi)

    return trades


start_at = datetime.datetime(2021, 7, 25)
end_at = datetime.datetime(2021, 9, 11)


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
expanded_timeline.head()

# |%%--%%| <twF6gWbIHX|MWZUTmPv42>
# |%%--%%| <MWZUTmPv42|tjbHOH24M2>
#
#
# from lib.fetch_ohlc import fetch_ohlc
#
# candles = fetch_ohlc(
#     timeframe=TimeBucket.h4,
#     trading_pair=("WBNB", "BUSD"),
#     chain_id=ChainId.bsc,
#     exchange_slug="pancakeswap-v2",
# )
# candles
# candles.to_parquet("WBNB-BUSD-h4.parquet")
