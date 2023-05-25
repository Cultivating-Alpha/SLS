from lib.fetch_ohlc import fetch_ohlc
from tradingstrategy.chain import ChainId
from tradingstrategy.timebucket import TimeBucket


candles = fetch_ohlc(
    trading_pair=("WBNB", "BUSD"),
    chain_id=ChainId.bsc,
    exchange_slug="pancakeswap-v3",
    timeframe=TimeBucket.h4,
)
candles
