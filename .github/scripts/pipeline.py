import pandas as pd
from tqdm import tqdm

from scripts.fetch_data import fetch_stock_list, fetch_daily, fetch_fundamental
from scripts.gate1_fundamental import gate1_score
from scripts.gate2_growth_value import gate2_priority
from scripts.gate3_timing import gate3_timing

def run_pipeline():
    stocks = fetch_stock_list()

    results = []

    for _, row in tqdm(stocks.iterrows(), total=len(stocks)):
        code = row["code"]
        name = row["name"]

        daily = fetch_daily(code)
        funda = fetch_fundamental(code)

        s1 = gate1_score(funda)
        if s1 < 6:
            continue

        s2 = gate2_priority(funda)
        if s2 == 0:
            continue

        timing = gate3_timing(daily)

        results.append({
            "code": code,
            "name": name,
            "gate1_score": s1,
            "gate2_priority": s2,
            "timing": timing
        })

    df = pd.DataFrame(results)
    df.sort_values(["gate2_priority", "gate1_score"], ascending=False, inplace=True)

    df.to_csv("outputs/decision_card.csv", index=False, encoding="utf-8-sig")
