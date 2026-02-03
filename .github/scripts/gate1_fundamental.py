import pandas as pd
import numpy as np

def gate1_score(funda: pd.DataFrame):
    if funda is None or len(funda) == 0:
        return 0

    row = funda.iloc[-1]

    score = 0

    # 生存
    if row.get("资产负债率", 100) < 70:
        score += 2
    if row.get("流动比率", 0) > 1:
        score += 1

    # 盈利质量
    if row.get("ROE", 0) > 10:
        score += 2
    if row.get("经营现金流量净额", -1) > 0:
        score += 2

    # 风险惩罚
    if row.get("净利润", -1) < 0:
        score -= 2

    return max(score, 0)
