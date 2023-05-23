from marshmallow.fields import Time
from tradingstrategy.client import Client


from pyarrow import Table
from tradingstrategy.chain import ChainId
from tradingstrategy.exchange import ExchangeUniverse
from tradingstrategy.pair import PandasPairUniverse, DEXPair

import pandas as pd
from tradingstrategy.timebucket import TimeBucket


def fetch_ohlc(
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
    pick_by_highest_vol=True,
    timeframe=TimeBucket.d1,
):
    client = Client.create_jupyter_client()
    # Fetch all exchange names, slugs and addresses
    exchange_universe: ExchangeUniverse = client.fetch_exchange_universe()

    # Fetch all trading pairs across all exchanges
    pair_table: Table = client.fetch_pair_universe()
    pair_universe = PandasPairUniverse(pair_table.to_pandas())

    exchange = exchange_universe.get_by_chain_and_slug(chain_id, exchange_slug)

    pair: DEXPair = pair_universe.get_one_pair_from_pandas_universe(
        exchange.exchange_id,
        trading_pair[0],
        trading_pair[1],
        pick_by_highest_vol=pick_by_highest_vol,
    )

    candles: pd.DataFrame = client.fetch_candles_by_pair_ids(
        {pair.pair_id},
        timeframe,
        progress_bar_description=f"Download data for {pair.get_ticker()}",
    )

    return candles


candles = fetch_ohlc(
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
    timeframe=TimeBucket.h4,
)
candles.drop(columns=["timestamp"], inplace=True)
candles
