"""
数据源保障方案 - 自动切换和重试机制
"""
import time
import random
import pandas as pd
from typing import Optional, Dict, Any, List
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProvider:
    """智能数据提供器 - 自动切换可用源"""
    
    def __init__(self):
        self.data_sources = {
            'primary': {
                'name': 'akshare',
                'module': None,
                'priority': 1,
                'last_success': None,
                'failure_count': 0
            },
            'secondary': {
                'name': 'baostock',
                'module': None,
                'priority': 2,
                'last_success': None,
                'failure_count': 0
            },
            'international': {
                'name': 'yfinance',
                'module': None,
                'priority': 3,
                'last_success': None,
                'failure_count': 0,
                'needs_proxy': True
            }
        }
        
        # 代理设置（如果需要）
        self.proxy_pool = [
            None,  # 直连尝试
            {'http': 'http://localhost:7890', 'https': 'http://localhost:7890'},
            {'http': 'socks5://localhost:1080', 'https': 'socks5://localhost:1080'}
        ]
        
        self.init_sources()
    
    def init_sources(self):
        """动态导入数据源模块"""
        try:
            import akshare as ak
            self.data_sources['primary']['module'] = ak
            logger.info("✅ Akshare 初始化成功")
        except ImportError as e:
            logger.warning(f"⚠️  Akshare 导入失败: {e}")
        
        try:
            import baostock as bs
            self.data_sources['secondary']['module'] = bs
            logger.info("✅ Baostock 初始化成功")
        except ImportError as e:
            logger.warning(f"⚠️  Baostock 导入失败: {e}")
        
        try:
            import yfinance as yf
            self.data_sources['international']['module'] = yf
            logger.info("✅ YFinance 初始化成功")
        except ImportError as e:
            logger.warning(f"⚠️  YFinance 导入失败: {e}")
    
    def get_available_source(self, source_type: str = 'auto'):
        """获取可用数据源"""
        if source_type != 'auto':
            return self.data_sources.get(source_type)
        
        # 按优先级和成功率自动选择
        available = []
        for key, source in self.data_sources.items():
            if source['module'] is not None:
                # 降低频繁失败源的优先级
                score = source['priority'] * 100 - source['failure_count'] * 10
                available.append((score, key, source))
        
        available.sort(key=lambda x: x[0], reverse=True)
        return available[0][2] if available else None
    
    def retry_with_fallback(self, max_retries=3):
        """重试装饰器，自动回退"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries):
                    source = self.get_available_source()
                    if not source:
                        raise ConnectionError("无可用数据源")
                    
                    try:
                        # 设置代理（如果需要）
                        if source.get('needs_proxy'):
                            proxy = random.choice(self.proxy_pool)
                            kwargs['proxy'] = proxy
                        
                        result = func(*args, **kwargs, data_source=source)
                        source['last_success'] = time.time()
                        source['failure_count'] = max(0, source['failure_count'] - 1)
                        return result
                    
                    except Exception as e:
                        last_error = e
                        source['failure_count'] += 1
                        logger.warning(f"尝试 {source['name']} 失败 ({attempt+1}/{max_retries}): {e}")
                        time.sleep(1 * (attempt + 1))  # 递增等待
                
                raise ConnectionError(f"所有数据源尝试失败: {last_error}")
            return wrapper
        return decorator
    
    @retry_with_fallback(max_retries=3)
    def get_stock_data(self, symbol: str, start_date: str, end_date: str, 
                      data_source: Optional[Dict] = None, **kwargs):
        """获取股票数据 - 自动切换源"""
        proxy = kwargs.get('proxy')
        
        if data_source['name'] == 'akshare':
            # Akshare 示例
            import akshare as ak
            try:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                       start_date=start_date, end_date=end_date,
                                       adjust="qfq")
                return df
            except Exception as e:
                # 尝试其他接口
                try:
                    df = ak.stock_us_daily(symbol=symbol)
                    return df
                except:
                    raise e
        
        elif data_source['name'] == 'baostock':
            # Baostock 示例
            import baostock as bs
            try:
                lg = bs.login()
                rs = bs.query_history_k_data_plus(
                    symbol,
                    "date,code,open,high,low,close,volume,amount",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",
                    adjustflag="2"
                )
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                df = pd.DataFrame(data_list, columns=rs.fields)
                bs.logout()
                return df
            except Exception as e:
                raise e
        
        elif data_source['name'] == 'yfinance':
            # YFinance 示例（可配代理）
            import yfinance as yf
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                return df
            except Exception as e:
                raise e
        
        else:
            raise ValueError(f"不支持的数据源: {data_source['name']}")
    
    def get_market_index(self, index_code: str = "sh000001"):
        """获取指数数据"""
        try:
            # 优先使用akshare
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol=index_code)
            return df
        except:
            # 备用方案
            return self.get_stock_data(index_code, 
                                     start_date="2020-01-01",
                                     end_date=time.strftime("%Y-%m-%d"))
    
    def get_financial_news(self, count: int = 10):
        """获取财经新闻"""
        try:
            import akshare as ak
            news = ak.stock_news_em(symbol="全部", count=count)
            return news
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")
            # 返回模拟数据
            return pd.DataFrame({
                '标题': [f'财经新闻{i}' for i in range(count)],
                '内容': [f'示例内容{i}' for i in range(count)],
                '时间': [pd.Timestamp.now() for _ in range(count)]
            })

# 全局实例
data_provider = DataProvider()

# 简化调用接口
def get_stock(symbol: str, start_date: str, end_date: str):
    """简化版股票数据获取"""
    return data_provider.get_stock_data(symbol, start_date, end_date)

def get_index(index_code: str = "sh000001"):
    """获取指数"""
    return data_provider.get_market_index(index_code)

def get_news(count: int = 10):
    """获取新闻"""
    return data_provider.get_financial_news(count)
