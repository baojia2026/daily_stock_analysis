import numpy as np

def gate3_timing(price_df):
    if price_df is None or len(price_df) < 20:
        return "NO"

    close = price_df["收盘"].values
    recent = close[-1]
    ma20 = close[-20:].mean()

    if recent < ma20 * 0.95:
        return "WATCH"   # 超跌
    if recent > ma20:
        return "YES"     # 修复
    return "NO"
