from tradingstrategy.client import Client
import pandas as pd


# |%%--%%| <T093EoGgQm|T7AVMSPzSx>

from tradingstrategy.chain import ChainId
from tradeexecutor.strategy.trading_strategy_universe import (
    load_all_data,
    TradingStrategyUniverse,
)
import datetime
from tradingstrategy.client import Client
from tradingstrategy.timebucket import TimeBucket
from tradeexecutor.strategy.universe_model import UniverseOptions
from tradeexecutor.strategy.execution_context import ExecutionContext
from tradeexecutor.analysis.trade_analyser import build_trade_analysis


def create_trading_universe(
    ts: datetime.datetime,
    client: Client,
    execution_context: ExecutionContext,
    universe_options: UniverseOptions,
    candle_time_bucket=TimeBucket.h4,
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
) -> TradingStrategyUniverse:
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

from tradeexecutor.strategy.cycle import CycleDuration
from tradeexecutor.strategy.strategy_module import (
    StrategyType,
    TradeRouting,
    ReserveCurrency,
)


from tradeexecutor.strategy.execution_context import ExecutionMode

# |%%--%%| <vYHcHf9jQ0|aq93a1FBrI>

from tradeexecutor.visual.single_pair import visualise_single_pair
from tradeexecutor.visual.equity_curve import calculate_equity_curve, calculate_returns
from tradeexecutor.analysis.advanced_metrics import (
    visualise_advanced_metrics,
    AdvancedMetricsMode,
)


class Backtester:
    def create_universe(
        self,
        timeframe=TimeBucket.h4,
        trading_pair=("WBNB", "BUSD"),
        chain_id=ChainId.bsc,
        exchange_slug="pancakeswap-v2",
    ):
        self.universe = create_trading_universe(
            datetime.datetime.utcnow(),
            client,
            ExecutionContext(mode=ExecutionMode.backtesting),
            UniverseOptions(),
            candle_time_bucket=timeframe,
            trading_pair=trading_pair,
            chain_id=chain_id,
            exchange_slug=exchange_slug,
        )

    def backtest(
        self,
        start_at,
        end_at,
        decide_trades,
        initial_deposit=10_000,
        cycle_duration=CycleDuration.cycle_16h,
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
        with pd.option_context("display.max_row", None):
            display(metrics)
        print("==========")
        print(f"Total return: {returns['Strategy']}")
        print(f"Max Drawdown: {dd['Strategy']}")

    def general_stats(self):
        analysis = build_trade_analysis(self.state.portfolio)

        summary = analysis.calculate_summary_statistics()

        with pd.option_context("display.max_row", None):
            display(summary.to_dataframe())
