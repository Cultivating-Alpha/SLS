from tradingstrategy.client import Client
import pandas as pd
import logging

from tradeexecutor.backtest.backtest_runner import run_backtest_inline
from tradeexecutor.strategy.cycle import CycleDuration
from tradeexecutor.strategy.strategy_module import (
    TradeRouting,
    ReserveCurrency,
)

from tradeexecutor.strategy.execution_context import ExecutionMode
from tradeexecutor.visual.single_pair import visualise_single_pair
from tradeexecutor.visual.equity_curve import calculate_equity_curve, calculate_returns
from tradeexecutor.analysis.advanced_metrics import (
    visualise_advanced_metrics,
    AdvancedMetricsMode,
)


from tradingstrategy.chain import ChainId
import datetime
from tradingstrategy.client import Client
from tradingstrategy.timebucket import TimeBucket
from tradeexecutor.strategy.universe_model import UniverseOptions
from tradeexecutor.strategy.execution_context import ExecutionContext
from tradeexecutor.analysis.trade_analyser import build_trade_analysis


from tradeexecutor.strategy.trading_strategy_universe import load_partial_data
from tradeexecutor.strategy.trading_strategy_universe import (
    TradingStrategyUniverse,
)

# |%%--%%| <T093EoGgQm|T7AVMSPzSx>


def create_trading_universe(
    client: Client,
    trading_pair,
    start_at,
    end_at,
    execution_context,
    universe_options,
    reserve_currency,
    candle_time_bucket=TimeBucket.h4,
    stop_loss_time_bucket=TimeBucket.h1,
) -> TradingStrategyUniverse:
    assert (
        not execution_context.mode.is_live_trading()
    ), f"Only strategy backtesting supported, got {execution_context.mode}"

    # Load data for our trading pair whitelist
    dataset = load_partial_data(
        client=client,
        time_bucket=candle_time_bucket,
        pairs=trading_pair,
        execution_context=execution_context,
        universe_options=universe_options,
        stop_loss_time_bucket=stop_loss_time_bucket,
        start_at=start_at,
        end_at=end_at,
    )

    # Filter down the dataset to the pairs we specified
    universe = TradingStrategyUniverse.create_multichain_universe_by_pair_descriptions(
        dataset,
        trading_pair,
        reserve_token_symbol=reserve_currency,
    )

    return universe


# |%%--%%| <T7AVMSPzSx|YurWRBJy2a>

from tradingstrategy.client import Client

client = Client.create_jupyter_client()

# |%%--%%| <YurWRBJy2a|vYHcHf9jQ0>


# |%%--%%| <vYHcHf9jQ0|aq93a1FBrI>


class Backtester:
    def __init__(
        self,
        candle_time_bucket=TimeBucket.h4,
        stop_loss_time_bucket=TimeBucket.m5,
        trading_pair=[(ChainId.ethereum, "uniswap-v3", "WETH", "USDC", 0.0005)],
        start_at=datetime.datetime(2023, 1, 1),
        end_at=datetime.datetime(2023, 6, 1),
        reserve_currency="USDC",
    ):
        self.universe = create_trading_universe(
            client,
            universe_options=UniverseOptions(),
            execution_context=ExecutionContext(mode=ExecutionMode.backtesting),
            candle_time_bucket=candle_time_bucket,
            stop_loss_time_bucket=stop_loss_time_bucket,
            trading_pair=trading_pair,
            start_at=start_at,
            end_at=end_at,
            reserve_currency=reserve_currency,
        )

    def backtest(
        self,
        start_at,
        end_at,
        decide_trades,
        initial_deposit=10_000,
        cycle_duration=CycleDuration.cycle_4h,
        reserve_currency=ReserveCurrency.busd,
        trade_routing=TradeRouting.pancakeswap_busd,
    ):
        self.start_at = start_at
        self.end_at = end_at

        state, _, debug_dump = run_backtest_inline(
            name="BNB/USD EMA crossover example",
            start_at=start_at,
            end_at=end_at,
            client=client,
            cycle_duration=cycle_duration,
            decide_trades=decide_trades,
            universe=self.universe,
            initial_deposit=initial_deposit,
            reserve_currency=reserve_currency,
            trade_routing=trade_routing,
            log_level=logging.WARNING,
        )
        self.state = state

        trade_count = len(list(state.portfolio.get_all_trades()))
        print(f"Backtesting completed, backtested strategy made {trade_count} trades")

    def plot(self):
        figure = visualise_single_pair(
            self.state,
            self.universe.universe.candles,
            start_at=self.start_at,
            end_at=self.end_at,
        )

        figure.show()

    def stats(self):
        equity = calculate_equity_curve(self.state)
        returns = calculate_returns(equity)
        metrics = visualise_advanced_metrics(returns, mode=AdvancedMetricsMode.full)

        returns = metrics.loc["Cumulative Return"]
        dd = metrics.loc["Max Drawdown"]
        # with pd.option_context("display.max_row", None):
        #     display(metrics)
        print("==========")
        print(f"Total return: {returns['Strategy']}")
        print(f"Max Drawdown: {dd['Strategy']}")

    def general_stats(self):
        analysis = build_trade_analysis(self.state.portfolio)

        summary = analysis.calculate_summary_statistics()

        with pd.option_context("display.max_row", None):
            display(summary.to_dataframe())
