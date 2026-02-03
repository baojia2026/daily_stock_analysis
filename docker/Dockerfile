# ===================================
# A股自选股智能分析系统 - Docker 镜像
# ===================================
# 基于 Python 3.11 slim 镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ==============================
# 安装系统依赖（newspaper3k / lxml 必需）
# ==============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# ==============================
# 安装 Python 依赖
# ==============================
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY *.py ./
COPY data_provider/ ./data_provider/
COPY web/ ./web/
COPY bot/ ./bot/
COPY src/ ./src/

# 创建数据目录
RUN mkdir -p /app/data /app/logs /app/reports

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/app/logs
ENV DATABASE_PATH=/app/data/stock_analysis.db

# WebUI
ENV WEBUI_HOST=0.0.0.0
ENV WEBUI_PORT=8000

# 暴露端口
EXPOSE 8000

# 数据卷
VOLUME ["/app/data", "/app/logs", "/app/reports"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || python -c "import sys; sys.exit(0)"

# 默认命令
CMD ["python", "main.py", "--schedule"]
