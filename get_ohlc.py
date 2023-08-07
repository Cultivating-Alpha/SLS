import pandas as pd
import requests
import mplfinance as mpf


def process_url(pair_id, exchange_type, time_bucket, start, old_df=None):
    url = f"https://tradingstrategy.ai/api/candles?pair_id={pair_id}&exchange_type={exchange_type}&time_bucket={time_bucket}&start={start}"
    # Perform the request
    response = requests.get(url)

    # Read the JSON data from the URL into a DataFrame
    _df = pd.read_json(response.text)

    if old_df is None:
        old_df = pd.DataFrame()
    df = pd.DataFrame()
    df["Open"] = _df["o"]
    df["High"] = _df["h"]
    df["Low"] = _df["l"]
    df["Close"] = _df["c"]
    df["Volume"] = _df["v"]
    df["Date"] = _df["ts"]

    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%dT%H:%M:%S")
    df.set_index("Date", inplace=True)

    df = pd.concat([old_df, df])

    now = pd.Timestamp.now()
    end_date = df.index[-1]
    diff = now - end_date

    if diff.days > 0:
        print("getting more")
        print(end_date.strftime("%Y-%m-%d"))
        return process_url(
            pair_id, exchange_type, time_bucket, end_date.strftime("%Y-%m-%d"), df
        )
    else:
        return df


# Set the URL and headers
# for tf in ['4h', '1h', '1d', '15m']:
#     url = f"https://tradingstrategy.ai/api/candles?pair_id=2854973&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
#     df = process_url(url)
#     df.to_parquet( f"./data/uniswap_v3-polygon-WETH-USDC-{tf}.parquet")
#
# for tf in ['4h', '1h', '1d', '15m']:
#     url = f"https://tradingstrategy.ai/api/candles?pair_id=2697765&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
#     df = process_url(url)
#     df.to_parquet( f"./data/uniswap_v3-ethereum-WETH-USDC-{tf}.parquet")
#
# for tf in ['4h', '1h', '1d', '15m']:
#     url = f"https://tradingstrategy.ai/api/candles?pair_id=2854997&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
#     df = process_url(url)
#     df.to_parquet( f"./data/uniswap_v3-polygon-WMATIC-USDC-{tf}.parquet")


# for tf in ["4h"]:
#     url = f"https://tradingstrategy.ai/api/candles?pair_id=2993973&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
#     df = process_url(url)
#     df.to_parquet(f"./data/uniswap_v3-arbitrum-WBTC-USDC-{tf}.parquet")
#
# for tf in ["4h"]:
#     url = f"https://tradingstrategy.ai/api/candles?pair_id=2991521&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
#     df = process_url(url)
#     df.to_parquet(f"./data/uniswap_v3-arbitrum-WETH-USDC-{tf}.parquet")


for tf in ["1h"]:
    pair_id = 93756
    exchange_type = "uniswap_v2"
    name = "quickswap_v3-polygon-WETH-USDC"

    df = process_url(pair_id, exchange_type, tf, "2011-11-04")
    df.to_parquet(f"./data/{name}-{tf}.parquet")

for tf in ["1h"]:
    pair_id = 239
    exchange_type = "uniswap_v2"
    name = "uniswap_v2-ethereum-WETH-USDC"

    df = process_url(pair_id, exchange_type, tf, "2011-11-04")
    df.to_parquet(f"./data/{name}-{tf}.parquet")

for tf in ["1h"]:
    pair_id = 2697765
    exchange_type = "uniswap_v3"
    name = "uniswap_v3-ethereum-WETH-USDC-1h"

    df = process_url(pair_id, exchange_type, tf, "2011-11-04")
    df.to_parquet(f"./data/{name}-{tf}.parquet")
