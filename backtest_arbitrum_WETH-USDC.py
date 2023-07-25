import pandas as pd
import datetime

from lib.ts_backtester import Backtester
from strategies.rsi_2.S_rsi_plot import plot

import pandas_ta as ta
from tradeexecutor.strategy.pandas_trader.position_manager import PositionManager
from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.chain import ChainId

# Set Jupyter Notebook output mode parameters
# Used to avoid warnings
from tradeexecutor.backtest.notebook import setup_charting_and_output

setup_charting_and_output()

from tradeexecutor.visual.equity_curve import calculate_equity_curve, calculate_returns
from tradeexecutor.visual.equity_curve import visualise_equity_curve


backtester = Backtester(
    candle_time_bucket=TimeBucket.h4,
    stop_loss_time_bucket=TimeBucket.m1,
    trading_pair=[(ChainId.arbitrum, "uniswap-v3", "WETH", "USDC", 0.0005)],
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

ma_long = 117
ma_short = 27
rsi_cutt = 3
atr_distance = 1
# DD = 10% -- CAGR = 28.8% -- Total = 33.%  Total/DD = 3.3

# DD = 10% -- CAGR = 28.8%

# ma_long = 520
# ma_short = 27
# rsi_cutt = 3
# atr_distance = 1
# # DD = 17 -- CAGR = 34.03 -- Total = 50.8 -- Total/DD = 2.99
#
# ma_long = 104
# ma_short = 28
# rsi_cutt = 3
# atr_distance = 1
# # DD = 10.8 -- CAGR = 25.9 -- Total = 30.8 -- Total/DD = 2.85


def get_signals(candles):
    close = candles["close"].iloc[-1]
    low = candles["low"].iloc[-1]

    # Calculate indicators
    sma_short = ta.sma(candles["close"], length=ma_short).iloc[-1]
    sma_long = ta.sma(candles["close"], length=ma_long).iloc[-1]
    rsi = ta.rsi(candles["close"], length=2).iloc[-1]
    atr = ta.atr(candles["high"], candles["low"], candles["close"], length=14).iloc[-1]

    # Calculate signals

    entry = close <= sma_short and close >= sma_long and rsi <= rsi_cutt
    exit = close > sma_short
    sl = low - atr * atr_distance
    sl_pct = float(round(sl / candles["open"].iloc[-1], 6))

    indicators = {
        "sma_short": sma_short,
        "sma_long": sma_long,
        "rsi": rsi,
        "atr": atr,
    }
    return entry, exit, sl, sl_pct, indicators


def calculate_size(state, close):
    cash = state.portfolio.get_current_cash()
    return cash * 0.99


current_sl = np.inf


def loop(timestamp, universe, state, pricing_model, cycle_debug_data):
    # The pair we are trading
    trades = []
    pair = universe.pairs.get_single()

    candles: pd.DataFrame = universe.candles.get_single_pair_data(
        timestamp, sample_count=ma_long
    )

    if len(candles) < ma_long:
        return trades

    current_price = candles["close"].iloc[-1]

    entry, exit, sl, sl_pct, indicators = get_signals(candles)
    global current_sl

    # Create a position manager helper class that allows us easily to create
    # opening/closing trades for different positions
    position_manager = PositionManager(timestamp, universe, state, pricing_model)
    buy_amount = calculate_size(state, current_price)

    if not position_manager.is_any_open():
        if entry:
            current_sl = sl
            trades += position_manager.open_1x_long(pair, buy_amount)
    else:
        if exit:
            current_sl = np.inf
            trades += position_manager.close_all()
        # elif current_price < current_sl:
        #     current_sl = np.inf
        #     trades += position_manager.close_all()

    plot(state, timestamp, indicators)

    return trades


# start_at = datetime.datetime(2021, 7, 1)
# start_at = datetime.datetime(2022, 8, 30)
start_at = datetime.datetime(2021, 11, 30)
end_at = datetime.datetime(2023, 6, 4)


backtester.backtest(start_at, end_at, loop)
backtester.stats()
backtester.general_stats()
# backtester.plot()


state = backtester.state
curve = calculate_equity_curve(state)
returns = calculate_returns(curve)
visualise_equity_curve(returns)
