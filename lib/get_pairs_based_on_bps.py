from tradingstrategy.client import Client
from tradingstrategy.stablecoin import ALL_STABLECOIN_LIKE
import pandas as pd


def get_pairs_based_on_bps(exchange="uniswap-v3", fee_tier=5):
    client = Client.create_jupyter_client()
    columnar_pair_table: Table = client.fetch_pair_universe()
    pairs_df = columnar_pair_table.to_pandas()
    low_fee_pairs: pd.DataFrame = pairs_df.loc[
        (pairs_df["exchange_slug"] == exchange) & (pairs_df["fee"] == fee_tier)  # BPS
    ]
    return low_fee_pairs


def filter_with_volume(pairs_df: pd.DataFrame, volume_threshold_30d=2_000_000):
    # Assume no volume data is zero volume
    pairs_df = pairs_df.fillna(0)
    volume_pairs = pairs_df.loc[pairs_df["buy_volume_30d"] >= volume_threshold_30d]
    return volume_pairs


def filter_not_stable_stable(pairs):
    return pairs.loc[~pairs["base_token_symbol"].isin(ALL_STABLECOIN_LIKE)]


# Example run
pairs = get_pairs_based_on_bps(exchange="uniswap-v3", fee_tier=5)
pairs = filter_with_volume(pairs, volume_threshold_30d=1_000_000)
pairs = filter_not_stable_stable(pairs)
pairs
pairs.columns


pairs[["base_token_symbol", "quote_token_symbol"]]

# |%%--%%| <I2DkwDoXG8|oY6HStlOgW>

# from lib.fetch_ohlc import fetch_ohlc
from tradingstrategy.chain import ChainId
from tradingstrategy.timebucket import TimeBucket

from tradeexecutor.strategy.trading_strategy_universe import (
    load_pair_data_for_single_exchange,
)
from tradeexecutor.strategy.execution_context import ExecutionContext, ExecutionMode

execution_context = ExecutionContext(
    mode=ExecutionMode.backtesting,
)

trading_pairs = {
    ("WBNB", "BUSD"),
    ("Cake", "WBNB"),
}
client = Client.create_jupyter_client()

dataset = load_pair_data_for_single_exchange(
    client,
    execution_context,
    TimeBucket.d1,
    ChainId.bsc,
    "pancakeswap-v2",
    trading_pairs,
    universe_options=UniverseOptions(),
)
