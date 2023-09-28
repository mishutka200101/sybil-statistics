import streamlit as st
import pandas as pd

from modules.worker import run_all


st.set_page_config(page_title="ZkSync Sybil")
st.title("ZkSync Sybil")

addresses_str = st.text_area(label='Insert addresses that splitted by ENTER')
addresses = addresses_str.split('\n')
addresses_stripped = [_.strip() for _ in addresses][:500]

if not addresses_str:
    st.stop()

try:
    data = run_all(addresses=addresses_stripped)
    columns = [
        'address',
        'ETH in USD',
        'USDC',
        'USDT',
        'txs',
        'SyncSwap',
        'Woofi',
        'Maverick',
        'Izumi',
        'SpaceFi',
        'Merkly'
    ]
    df = pd.DataFrame(data=data, columns=columns)
    df.index += 1
    st.dataframe(data=df, use_container_width=True)

    eth_value = sum(df["ETH in USD"])
    usdt_value = sum(df["USDT"])
    usdc_value = sum(df["USDC"])
    total_sum = eth_value + usdt_value + usdc_value
    st.title(f"Total balance is: {round(total_sum, 2)}$")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
