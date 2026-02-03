import akshare as ak
import pandas as pd
from pathlib import Path

BASE = Path("data/raw")
BASE.mkdir(parents=True, exist_ok=True)

def fetch_stock_list():
    df = ak.stock_info_a_code_name()
    return df[["code", "name"]]

def fetch_daily(symbol):
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        return df
    except:
        return None

def fetch_fundamental(symbol):
    try:
        df = ak.stock_a_lg_indicator(symbol=symbol)
        return df
    except:
        return None
