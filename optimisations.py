import pandas as pd
import numpy as np


def load_data(data="BTC"):
    df = pd.read_parquet(f"./optimisations/{data}.parquet")
    return df


btc = load_data("BTC")  # There is a total of 1.8M rows
eth = load_data("ETH")  # There is a total of 5.4M rows

# |%%--%%| <fn6jtakTMf|Ml645FTVLN>

# How to sort the arrays
sorted_by_dd = btc.sort_values(by=["dd"], ascending=False)
sorted_by_final_value = btc.sort_values(by=["final_value"], ascending=False)
sorted_by_ratio = btc.sort_values(by=["ratio"], ascending=False)
"""
Ratio = final_value / dd
A ratio > 3 means that we don't drawdown more than 30% of max equity
"""

sorted_by_ratio.head(10)

# |%%--%%| <Ml645FTVLN|9jQ1Bhbi1a>


def find_index_or_param(arr, target):
    """
    Use this to look for a certain parameter combination inside the dataframe
    """
    df = arr.copy()
    df.reset_index(inplace=True)
    for i, item in enumerate(df["index"].values):
        if np.array_equal(item, target_element):
            return i


def print_values_at_index(df, index):
    print(df.reset_index().iloc[index])


"""
Here is an example of to look for the index of a certain parameter combination
As well as how to print the values at that index
"""
target_element = [112, 35, 3, 0.5]
index = find_index_or_param(btc, target_element)
print(index)

print_values_at_index(btc, index)
