from tradingstrategy.client import Client
import pandas as pd


def get_pairs_based_on_bps(exchange="uniswap-v3", fee_tier=5):
    client = Client.create_jupyter_client()
    columnar_pair_table: Table = client.fetch_pair_universe()
    pairs_df = columnar_pair_table.to_pandas()
    low_fee_pairs: pd.DataFrame = pairs_df.loc[
        (pairs_df["exchange_slug"] == exchange) & (pairs_df["fee"] == fee_tier)  # BPS
    ]
    return low_fee_pairs


# Example run
pairs = get_pairs_based_on_bps(exchange="uniswap-v3", fee_tier=5)
