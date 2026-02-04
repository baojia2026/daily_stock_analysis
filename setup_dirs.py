#!/usr/bin/env python3
"""
创建必要目录结构
"""
import os
import sys

def create_directories():
    """创建项目目录结构"""
    directories = [
        'data/raw',
        'data/processed',
        'data/cache',
        'data/models',
        'logs',
        'config',
        'reports/daily',
        'reports/weekly',
        'reports/monthly',
        'temp',
        'tests/data',
        'docs/images',
    ]
    
    print("📁 创建项目目录结构...")
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  ✅ 创建: {directory}")
            
            gitkeep_file = os.path.join(directory, '.gitkeep')
            with open(gitkeep_file, 'w') as f:
                f.write('# Keep directory in git\n')
                
        except Exception as e:
            print(f"  ❌ 创建失败 {directory}: {e}")
    
    config_files = {
        'config/config.yaml': """
project:
  name: "股票分析系统"
  version: "1.0.0"

data_sources:
  primary: "akshare"
  fallback: "baostock"
  cache_days: 7

apis:
  openai:
    base_url: "https://api.openai.com/v1"
  anthropic:
    base_url: "https://api.anthropic.com"
    
analysis:
  default_period: "30d"
  indicators: ["MA", "RSI", "MACD"]
""",
        
        'config/secrets.example.yaml': """
openai_api_key: "your-openai-key-here"
anthropic_api_key: "your-anthropic-key-here"
google_api_key: "your-google-key-here"

database_url: "sqlite:///data/finance.db"

proxy:
  enabled: false
  http_proxy: "http://localhost:7890"
  https_proxy: "http://localhost:7890"
""",
        
        '.env.example': """
DEBUG=true
LOG_LEVEL=INFO
DATA_CACHE_ENABLED=true
MAX_CACHE_DAYS=7

PREFERRED_DATA_SOURCE=akshare
FALLBACK_DATA_SOURCE=baostock

ANALYSIS_PERIOD=30
MIN_DATA_POINTS=20
""",
        
        '.gitignore': """
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

venv/
env/
.env
.venv

data/
*.db
*.sqlite
*.csv
*.pkl
*.pickle

logs/
*.log

.vscode/
.idea/
*.swp
*.swo

.DS_Store
Thumbs.db

config/secrets.yaml
.env
"""
    }
    
    print("\n📄 创建配置文件...")
    for file_path, content in config_files.items():
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n')
            print(f"  ✅ 创建: {file_path}")
        except Exception as e:
            print(f"  ❌ 创建失败 {file_path}: {e}")
    
    print("\n🎉 目录结构创建完成！")
    print("\n下一步：")
    print("1. 运行: pip install -r requirements.txt")
    print("2. 复制 config/secrets.example.yaml 为 config/secrets.yaml")
    print("3. 复制 .env.example 为 .env")
    print("4. 运行: python main.py")

if __name__ == "__main__":
    create_directories()
