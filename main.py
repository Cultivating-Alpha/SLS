import pandas as pd
from typing import List, Dict
from typing import Optional

from tradeexecutor.state.visualisation import PlotKind
from tradeexecutor.state.trade import TradeExecution
from tradeexecutor.strategy.pricing_model import PricingModel
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.state.state import State
from tradingstrategy.universe import Universe

from pandas_ta.overlap import ema

# |%%--%%| <SZUpNPeecJ|0odf4siOwY>

batch_size = 90
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
    slow_ema_series = ema(close, length=slow_ema_candle_count)
    fast_ema_series = ema(close, length=fast_ema_candle_count)

    if slow_ema_series is None or fast_ema_series is None:
        return None, None

    slow_ema = slow_ema_series.iloc[-1]
    fast_ema = fast_ema_series.iloc[-1]

    return fast_ema, slow_ema


def calculate_size(state):
    # How much cash we have in the hand
    cash = state.portfolio.get_current_cash()
    return cash * position_size


def loop(
    timestamp: pd.Timestamp,
    universe: Universe,
    state: State,
    pricing_model: PricingModel,
    cycle_debug_data: Dict,
) -> List[TradeExecution]:
    # The pair we are trading
    pair = universe.pairs.get_single()

    fast_ema, slow_ema = calculate_indicators(universe, timestamp)
    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=batch_size
    )

    # We have data for open, high, close, etc.
    # We only operate using candle close values in this strategy.
    close = candles["close"]

    if fast_ema is None or slow_ema is None:
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

    if current_price >= slow_ema:
        # Entry condition:
        # Close price is higher than the slow EMA
        if not position_manager.is_any_open():
            buy_amount = calculate_size(state)
            trades += position_manager.open_1x_long(pair, buy_amount)
    elif fast_ema >= slow_ema:
        # Exit condition:
        # Fast EMA crosses slow EMA
        if position_manager.is_any_open():
            trades += position_manager.close_all()

    # Visualize strategy
    # See available Plotly colours here
    # https://community.plotly.com/t/plotly-colours-list/11730/3?u=miohtama
    visualisation = state.visualisation
    visualisation.plot_indicator(
        timestamp,
        "BB upper",
        PlotKind.technical_indicator_on_price,
        slow_ema,
        colour="darkblue",
    )
    visualisation.plot_indicator(
        timestamp,
        "BB lower",
        PlotKind.technical_indicator_on_price,
        fast_ema,
        colour="#003300",
    )

    return trades


# |%%--%%| <0odf4siOwY|yQB6fLcUWK>

import datetime
from ts_backtester import Backtester
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
backtester.stats()
# |%%--%%| <yQB6fLcUWK|jxQSz2zcWR>

backtester.plot()
