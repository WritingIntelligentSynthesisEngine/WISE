FROM ghcr.io/astral-sh/uv:debian-slim

# 设置工作目录
WORKDIR /workspace

# 下载 python
RUN uv --no-cache python install 3.13

# 复制环境配置
COPY pyproject.toml uv.lock /workspace/

# 同步依赖
RUN uv --no-cache sync --frozen

# 复制源码
COPY . /workspace
