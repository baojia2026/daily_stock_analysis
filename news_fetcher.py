"""
新闻获取工具 - 解决newspaper3k依赖问题
"""
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsFetcher:
    """新闻获取器（不依赖newspaper3k）"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_finance_news(self, source: str = "sina", limit: int = 10) -> List[Dict]:
        """获取财经新闻"""
        if source == "sina":
            return self._fetch_sina_news(limit)
        elif source == "eastmoney":
            return self._fetch_eastmoney_news(limit)
        elif source == "jin10":
            return self._fetch_jin10_news(limit)
        else:
            return self._fetch_sina_news(limit)
    
    def _fetch_sina_news(self, limit: int) -> List[Dict]:
        """从新浪财经获取新闻"""
        try:
            url = "http://finance.sina.com.cn/stock/"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            news_list = []
            news_items = soup.select('.news-item, .blk_02 a, .blk_03 a')[:limit]
            
            for item in news_items:
                title = item.text.strip()
                link = item.get('href')
                if link and not link.startswith('http'):
                    link = 'http://finance.sina.com.cn' + link
                
                if title and link:
                    news_list.append({
                        'title': title,
                        'url': link,
                        'source': '新浪财经',
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取新浪新闻失败: {e}")
            return []
    
    def _fetch_eastmoney_news(self, limit: int) -> List[Dict]:
        """从东方财富获取新闻"""
        try:
            url = "http://news.eastmoney.com/"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            news_list = []
            news_items = soup.select('.newslist a, .em-news-list a')[:limit]
            
            for item in news_items:
                title = item.text.strip()
                link = item.get('href')
                if title and link and 'http' in link:
                    news_list.append({
                        'title': title,
                        'url': link,
                        'source': '东方财富',
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取东方财富新闻失败: {e}")
            return []
    
    def _fetch_jin10_news(self, limit: int) -> List[Dict]:
        """从金十数据获取快讯"""
        try:
            url = "https://www.jin10.com/"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            news_list = []
            news_items = soup.select('.jin-flash-item, .flash-item')[:limit]
            
            for item in news_items:
                title_elem = item.select_one('.jin-flash-content, .flash-content')
                time_elem = item.select_one('.jin-flash-time, .flash-time')
                
                if title_elem:
                    title = title_elem.text.strip()
                    time_text = time_elem.text.strip() if time_elem else ""
                    
                    news_list.append({
                        'title': title,
                        'time': time_text,
                        'source': '金十数据',
                        'type': '快讯'
                    })
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取金十数据失败: {e}")
            return []
    
    def get_article_content(self, url: str) -> Optional[Dict]:
        """获取文章详细内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            content_selectors = [
                '.article-content',
                '.article',
                '.content',
                '.main-content',
                '#artibody',
                '.article-body'
            ]
            
            content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True, separator='\n')
                    break
            
            if not content:
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            
            title = soup.title.string if soup.title else ""
            
            return {
                'title': title,
                'content': content[:5000] if content else "",
                'url': url,
                'length': len(content) if content else 0
            }
            
        except Exception as e:
            logger.error(f"获取文章内容失败 {url}: {e}")
            return None

if __name__ == "__main__":
    fetcher = NewsFetcher()
    
    print("获取新浪财经新闻:")
    news = fetcher.fetch_finance_news("sina", 5)
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   来源: {item['source']} | 时间: {item['time']}")
        print(f"   链接: {item['url']}\n")
