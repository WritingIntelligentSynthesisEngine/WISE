FROM ghcr.io/astral-sh/uv:debian-slim

# 设置工作目录
WORKDIR /workspace

# 复制环境配置
COPY pyproject.toml uv.lock ./

# 同步依赖
RUN uv sync --frozen --no-dev --no-cache

# 复制源码
COPY . .
