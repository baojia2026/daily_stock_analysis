# =========================
# main.py  【最终稳定版】
# =========================

# 1️⃣ 加载 .env（本地开发用，GitHub Actions 下不会生效但不影响）
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import logging
from datetime import datetime

# 2️⃣ 基础日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# 3️⃣ 打印关键环境变量状态（不打印值，只打印是否存在）
logger.info("========== 环境变量检查 ==========")
logger.info(f"OPENAI_API_KEY 是否存在：{'是' if os.getenv('OPENAI_API_KEY') else '否'}")
logger.info(f"TUSHARE_TOKEN 是否存在：{'是' if os.getenv('TUSHARE_TOKEN') else '否'}")
logger.info("===================================")

# 4️⃣ 引入项目核心 Pipeline（⚠️ 注意：是 src，不是 scripts）
try:
    from src.core.pipeline import StockAnalysisPipeline
except Exception as e:
    logger.error("❌ Pipeline 导入失败，请确认 src 目录结构未被改动")
    raise e


def main():
    logger.info("========== 启动每日股票分析系统 ==========")

    # 5️⃣ 初始化分析管线
    pipeline = StockAnalysisPipeline()

    # 6️⃣ 当前测试股票（后续你可以换成自选股 / 全市场）
    stock_list = ["000001"]

    results = []

    for code in stock_list:
        try:
            logger.info(f"开始分析股票：{code}")
            result = pipeline.run(code)
            results.append(result)
        except Exception as e:
            logger.error(f"{code} 分析失败：{e}", exc_info=True)

    logger.info("========== 分析完成 ==========")

    # 7️⃣ 简要输出结果（确保日志里能看到）
    for r in results:
        logger.info(f"分析结果：{r}")

    logger.info("程序执行结束")


if __name__ == "__main__":
    main()
