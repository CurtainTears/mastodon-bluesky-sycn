# 社交媒体同步工具

## 项目描述

这是一个用于在Bluesky和Mastodon之间同步帖子的工具。它允许用户自动将他们在一个平台上发布的内容同步到另一个平台,从而保持两个社交媒体账户的一致性。

## 主要功能

- 从Bluesky同步帖子到Mastodon
- 从Mastodon同步帖子到Bluesky
- 管理同步状态,避免重复同步
- 支持Docker部署

## 文件结构

- `src/bluesky_to_mastodon_sync.py`: 处理从Bluesky到Mastodon的同步逻辑
- `src/mastodon_to_bluesky_sync.py`: 处理从Mastodon到Bluesky的同步逻辑
- `src/sync_status_manager.py`: 管理同步状态
- `src/main.py`: 主程序入口
- `src/sync_tool.py`: 同步工具的核心功能
- `Dockerfile`: 用于构建Docker镜像
- `.github/workflows/docker-build.yml`: GitHub Actions工作流,用于自动构建和推送Docker镜像

## 如何使用

1. 克隆仓库
2. 配置环境变量(Bluesky和Mastodon的API密钥等)
3. 创建虚拟环境
4. 安装依赖
5. 运行 `python src/main.py` 或使用Docker部署

```
git clone https://github.com/yourusername/bluesky-to-mastodon-sync.git
cd bluesky-to-mastodon-sync
#配置环境变量
cp .env.example .env
#创建虚拟环境
python -m venv venv
source venv/bin/activate
#安装依赖
pip install -r requirements.txt
#运行
python src/main.py
```

## Docker部署

```
#拉取镜像
docker pull ghcr.io/curtaintears/bluesky-to-mastodon-sync:latest
#运行
docker run
  -d
  -e 'MASTODON_ACCESS_TOKEN'='xxxx'
  -e 'MASTODON_INSTANCE_URL'='https://example.com'
  -e 'BLUESKY_INSTANCE_URL'=''
  -e 'BLUESKY_USERNAME'='xxx.bsky.social'
  -e 'BLUESKY_PASSWORD'=''
  -e 'SYNC_INTERVAL'='300'
  -e 'FROM_MASTODON_AT'='@xxx@example.com'
  -e 'FROM_BLUESKY_AT'='@xxx.bsky.social'
  -v ./data:/app/data:'rw' 
  'muhosia/mastodon-bluesky-sync:latest'
```
# 环境变量说明

## 必填
- MASTODON_ACCESS_TOKEN= #你的Mastodon访问令牌
- MASTODON_INSTANCE_URL= #你的Mastodon实例URL
- BLUESKY_INSTANCE_URL= #你的Bluesky实例URL，留空则使用官方的Bluesky实例
- BLUESKY_USERNAME= #你的Bluesky用户名
- BLUESKY_PASSWORD= #你的Bluesky密码,应用专用密码
- SYNC_INTERVAL=300 #同步间隔，单位秒，默认5分钟

## 可选
- FROM_MASTODON_AT= #从Mastodon同步到Bluesky时，添加的@用户名
- FROM_BLUESKY_AT= #从Bluesky同步到Mastodon时，添加的@用户名
