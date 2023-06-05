from marshmallow.fields import Time
from tradingstrategy.client import Client


from pyarrow import Table
from tradingstrategy.chain import ChainId
from tradingstrategy.timebucket import TimeBucket
from tradingstrategy.exchange import ExchangeUniverse
from tradingstrategy.pair import PandasPairUniverse, DEXPair

import pandas as pd


def fetch_ohlc(
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v2",
    pick_by_highest_vol=True,
    timeframe=TimeBucket.d1,
    fee_tier=0.0005,
):
    client = Client.create_jupyter_client()
    # Fetch all exchange names, slugs and addresses
    exchange_universe: ExchangeUniverse = client.fetch_exchange_universe()

    # Fetch all trading pairs across all exchanges
    pair_table: Table = client.fetch_pair_universe()
    pair_universe = PandasPairUniverse(pair_table.to_pandas())

    exchange = exchange_universe.get_by_chain_and_slug(chain_id, exchange_slug)
    print(exchange)

    pair: DEXPair = pair_universe.get_one_pair_from_pandas_universe(
        exchange.exchange_id,
        trading_pair[0],
        trading_pair[1],
        pick_by_highest_vol=pick_by_highest_vol,
        fee_tier=fee_tier,
    )

    candles: pd.DataFrame = client.fetch_candles_by_pair_ids(
        {pair.pair_id},
        timeframe,
        progress_bar_description=f"Download data for {pair.get_ticker()}",
    )
    candles.drop(columns=["timestamp"], inplace=True)

    return candles


candles = fetch_ohlc(
    trading_pair=("WETH", "USDC"),
    chain_id=ChainId.ethereum,
    exchange_slug="uniswap-v3",
    timeframe=TimeBucket.h4,
)
candles.to_parquet("uniswap-v3-WETH-USDC-h4.parquet")
candles

# Get PancakeSwap exchange,
# for the full exchange list see https://tradingstrategy.ai/trading-view/exchanges
pancake = exchange_universe.get_by_chain_and_slug(ChainId.bsc, "pancakeswap-v2")

# Because there can be multiple trading pairs with same tickers,
# we pick the genuine among the scams based on its trading volume
wbnb_busd_pair = pair_universe.get_one_pair_from_pandas_universe(
    pancake.exchange_id,
    "WBNB",
    "BUSD",
    pick_by_highest_vol=True,
    )

print("WBNB address is", wbnb_busd_pair.base_token_address)
print("BUSD address is", wbnb_busd_pair.quote_token_address)
print("WBNB-BUSD pair contract address is", wbnb_busd_pair.address)
