from tradingstrategy.client import Client
import pandas as pd


def get_pairs_basedon_bps(exchange="uniswap-v3", fee_tier=5):
    client = Client.create_jupyter_client()
    columnar_pair_table: Table = client.fetch_pair_universe()
    pairs_df = columnar_pair_table.to_pandas()
    low_fee_pairs: pd.DataFrame = pairs_df.loc[
        (pairs_df["exchange_slug"] == exchange) & (pairs_df["fee"] == fee_tier)  # BPS
    ]
    return low_fee_pairs


pairs = get_pairs_basedon_bps(exchange="uniswap-v3", fee_tier=5)
pairs

# |%%--%%| <koRKQozxKf|T093EoGgQm>

from typing import List, Dict


from tradeexecutor.state.visualisation import PlotKind
from tradeexecutor.state.trade import TradeExecution
from tradeexecutor.strategy.pricing_model import PricingModel
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradeexecutor.state.state import State
from tradingstrategy.universe import Universe

from pandas_ta.overlap import ema

batch_size = 90
slow_ema_candle_count = 15
fast_ema_candle_count = 5
position_size = 0.10


def decide_trades(
    timestamp: pd.Timestamp,
    universe: Universe,
    state: State,
    pricing_model: PricingModel,
    cycle_debug_data: Dict,
) -> List[TradeExecution]:
    """The brain function to decide the trades on each trading strategy cycle.

    - Reads incoming execution state (positions, past trades)

    - Reads the current universe (candles)

    - Decides what to do next

    - Outputs strategy thinking for visualisation and debug messages

    :param timestamp:
        The Pandas timestamp object for this cycle. Matches
        trading_strategy_cycle division.
        Always truncated to the zero seconds and minutes, never a real-time clock.

    :param universe:
        Trading universe that was constructed earlier.

    :param state:
        The current trade execution state.
        Contains current open positions and all previously executed trades, plus output
        for statistics, visualisation and diangnostics of the strategy.

    :param pricing_model:
        Pricing model can tell the buy/sell price of the particular asset at a particular moment.

    :param cycle_debug_data:
        Python dictionary for various debug variables you can read or set, specific to this trade cycle.
        This data is discarded at the end of the trade cycle.

    :return:
        List of trade instructions in the form of :py:class:`TradeExecution` instances.
        The trades can be generated using `position_manager` but strategy could also hand craft its trades.
    """

    # The pair we are trading
    pair = universe.pairs.get_single()

    # How much cash we have in the hand
    cash = state.portfolio.get_current_cash()

    # Get OHLCV candles for our trading pair as Pandas Dataframe.
    # We could have candles for multiple trading pairs in a different strategy,
    # but this strategy only operates on single pair candle.
    # We also limit our sample size to N latest candles to speed up calculations.
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
        # Cannot calculate EMA, because
        # not enough samples in backtesting
        return []

    slow_ema = slow_ema_series.iloc[-1]
    fast_ema = fast_ema_series.iloc[-1]

    # Get the last close price from close time series
    # that's Pandas's Series object
    # https://pandas.pydata.org/docs/reference/api/pandas.Series.iat.html
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
            buy_amount = cash * position_size
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


# |%%--%%| <T093EoGgQm|T7AVMSPzSx>

from typing import Optional
from tradeexecutor.strategy.trading_strategy_universe import (
    load_all_data,
    TradingStrategyUniverse,
)
from tradeexecutor.strategy.execution_context import ExecutionContext
from tradeexecutor.strategy.universe_model import UniverseOptions
from tradingstrategy.client import Client
import datetime

from tradingstrategy.chain import ChainId

trading_pair = ("WBNB", "BUSD")
chain_id = ChainId.bsc
exchange_slug = "pancakeswap-v2"


def create_trading_universe(
    ts: datetime.datetime,
    client: Client,
    execution_context: ExecutionContext,
    universe_options: UniverseOptions,
) -> TradingStrategyUniverse:
    """Creates the trading universe where the strategy trades.

    If `execution_context.live_trading` is true then this function is called for
    every execution cycle. If we are backtesting, then this function is
    called only once at the start of backtesting and the `decide_trades`
    need to deal with new and deprecated trading pairs.

    As we are only trading a single pair, load data for the single pair only.

    :param ts:
        The timestamp of the trading cycle. For live trading,
        `create_trading_universe` is called on every cycle.
        For backtesting, it is only called at the start

    :param client:
        Trading Strategy Python client instance.

    :param execution_context:
        Information how the strategy is executed. E.g.
        if we are live trading or not.

    :param candle_timeframe_override:
        Allow the backtest framework override what candle size is used to backtest the strategy
        without editing the strategy Python source code file.

    :return:
        This function must return :py:class:`TradingStrategyUniverse` instance
        filled with the data for exchanges, pairs and candles needed to decide trades.
        The trading universe also contains information about the reserve asset,
        usually stablecoin, we use for the strategy.
    """

    # Load all datas we can get for our candle time bucket
    dataset = load_all_data(
        client, candle_time_bucket, execution_context, universe_options
    )

    # Filter down to the single pair we are interested in
    universe = TradingStrategyUniverse.create_single_pair_universe(
        dataset,
        chain_id,
        exchange_slug,
        trading_pair[0],
        trading_pair[1],
    )

    return universe


# |%%--%%| <T7AVMSPzSx|YurWRBJy2a>

from tradingstrategy.client import Client

client = Client.create_jupyter_client()

# |%%--%%| <YurWRBJy2a|vYHcHf9jQ0>

import logging

from tradeexecutor.backtest.backtest_runner import run_backtest_inline
from tradingstrategy.timebucket import TimeBucket

from tradeexecutor.strategy.cycle import CycleDuration
from tradeexecutor.strategy.strategy_module import (
    StrategyType,
    TradeRouting,
    ReserveCurrency,
)

trading_strategy_cycle = CycleDuration.cycle_16h
start_at = datetime.datetime(2021, 6, 1)
end_at = datetime.datetime(2022, 1, 1)
reserve_currency = ReserveCurrency.busd
trade_routing = TradeRouting.pancakeswap_busd
candle_time_bucket = TimeBucket.h4

# Start with 10,000 USD
initial_deposit = 10_000

from tradeexecutor.strategy.execution_context import ExecutionMode

universe = create_trading_universe(
    datetime.datetime.utcnow(),
    client,
    ExecutionContext(mode=ExecutionMode.backtesting),
    UniverseOptions(),
)

state, universe, debug_dump = run_backtest_inline(
    name="BNB/USD EMA crossover example",
    start_at=start_at,
    end_at=end_at,
    client=client,
    cycle_duration=trading_strategy_cycle,
    decide_trades=decide_trades,
    universe=universe,
    initial_deposit=initial_deposit,
    reserve_currency=reserve_currency,
    trade_routing=trade_routing,
    log_level=logging.WARNING,
)

trade_count = len(list(state.portfolio.get_all_trades()))
print(f"Backtesting completed, backtested strategy made {trade_count} trades")
# |%%--%%| <vYHcHf9jQ0|aq93a1FBrI>

from tradeexecutor.visual.single_pair import visualise_single_pair

universe.universe.candles
figure = visualise_single_pair(
    state, universe.universe.candles, start_at=start_at, end_at=end_at
)

figure.show()
