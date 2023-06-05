import pandas as pd
import requests
import mplfinance as mpf


def process_url(url):
    # Perform the request
    response = requests.get(url)

    # Read the JSON data from the URL into a DataFrame
    _df = pd.read_json(response.text)

    df = pd.DataFrame()
    df['Open'] = _df['o']
    df['High'] = _df['h']
    df['Low'] = _df['l']
    df['Close'] = _df['c']
    df['Volume'] = _df['v']
    df['Date'] = _df['ts']

    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%dT%H:%M:%S")
    df.set_index("Date", inplace=True)
    return df


# Set the URL and headers
for tf in ['4h', '1h', '1d', '15m']:
    url = f"https://tradingstrategy.ai/api/candles?pair_id=2854973&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
    df = process_url(url)
    df.to_parquet( f"./data/uniswap_v3-polygon-WETH-USDC-{tf}.parquet")

for tf in ['4h', '1h', '1d', '15m']:
    url = f"https://tradingstrategy.ai/api/candles?pair_id=2697765&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
    df = process_url(url)
    df.to_parquet( f"./data/uniswap_v3-ethereum-WETH-USDC-{tf}.parquet")

for tf in ['4h', '1h', '1d', '15m']:
    url = f"https://tradingstrategy.ai/api/candles?pair_id=2854997&exchange_type=uniswap_v3&time_bucket={tf}&start=2011-11-04"
    df = process_url(url)
    df.to_parquet( f"./data/uniswap_v3-polygon-WMATIC-USDC-{tf}.parquet")
