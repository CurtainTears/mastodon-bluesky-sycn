# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim



# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY src/ ./src/
COPY data/ ./data/
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量（这些将被 Docker 运行时的环境变量覆盖）
ENV MASTODON_INSTANCE_URL=""
ENV MASTODON_ACCESS_TOKEN=""
ENV BLUESKY_USERNAME=""
ENV BLUESKY_PASSWORD=""

# 运行应用
CMD ["python", "src/main.py"]

