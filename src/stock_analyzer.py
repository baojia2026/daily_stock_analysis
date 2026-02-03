from dataclasses import dataclass
import akshare as ak
import pandas as pd


@dataclass
class TrendAnalysisResult:
    code: str
    passed: bool
    score: float
    reason: str


class StockTrendAnalyzer:

    def __init__(self):
        pass

    def analyze(self, code: str) -> TrendAnalysisResult:
        try:
            # ========= 第一关：生存 & 价值 =========
            df = ak.stock_financial_analysis_indicator(symbol=code)

            if df is None or df.empty:
                return TrendAnalysisResult(code, False, 0, "无财务数据")

            latest = df.iloc[-1]
            score = 0

            roe = latest.get("净资产收益率", 0)
            debt = latest.get("资产负债率", 100)
            gross = latest.get("销售毛利率", 0)
            profit_growth = latest.get("净利润增长率", 0)

            if roe > 8:
                score += 2
            if debt < 60:
                score += 2
            if gross > 20:
                score += 2
            if profit_growth > 0:
                score += 2

            if score < 7.5:
                return TrendAnalysisResult(code, False, score, "未通过第一关")

            # ========= 第三关：短线修复 =========
            k = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")

            if k is None or k.empty or len(k) < 10:
                return TrendAnalysisResult(code, False, score, "K线不足")

            latest_k = k.iloc[-1]
            prev_k = k.iloc[-2]
            vol_mean = k["成交量"].rolling(5).mean().iloc[-1]

            if latest_k["收盘"] <= prev_k["收盘"]:
                return TrendAnalysisResult(code, False, score, "未反弹")

            if latest_k["成交量"] <= vol_mean:
                return TrendAnalysisResult(code, False, score, "无放量")

            return TrendAnalysisResult(code, True, score, "通过 1 + 3 关")

        except Exception as e:
            return TrendAnalysisResult(code, False, 0, f"异常: {e}")
