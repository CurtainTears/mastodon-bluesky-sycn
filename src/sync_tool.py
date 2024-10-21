from dotenv import load_dotenv
load_dotenv()  # 加载环境变量

import os
import logging
import time
from mastodon import Mastodon
from atproto import Client
from atproto_client.exceptions import InvokeTimeoutError
from mastodon_to_bluesky_sync import MastodonToBlueskySyncer
from bluesky_to_mastodon_sync import BlueskyToMastodonSyncer
from sync_status_manager import SyncStatusManager
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个带有超时设置的HTTP客户端
http_client = httpx.Client(timeout=30)

class SyncTool:
    def __init__(self):
        # 初始化Mastodon客户端
        mastodon_instance_url = os.environ.get('MASTODON_INSTANCE_URL', '')
        if not mastodon_instance_url.startswith('http'):
            mastodon_instance_url = f'https://{mastodon_instance_url}'
        
        self.mastodon = Mastodon(
            access_token=os.environ.get('MASTODON_ACCESS_TOKEN'),
            api_base_url=mastodon_instance_url
        )

        # 初始化Bluesky客户端
        bluesky_username = os.environ.get('BLUESKY_USERNAME', '')
        bluesky_password = os.environ.get('BLUESKY_PASSWORD', '')
        self.bluesky = Client()        
        
        # Bluesky登录，带有重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.bluesky.login(bluesky_username, bluesky_password)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Bluesky登录尝试 {attempt + 1} 失败：{str(e)}。5秒后重试...")
                    time.sleep(5)
                else:
                    logging.error("多次尝试后仍无法登录Bluesky。")
                    raise
        
        # 初始化同步状态管理器和同步器
        self.sync_status_manager = SyncStatusManager()
        self.mastodon_to_bluesky_syncer = MastodonToBlueskySyncer(self.mastodon, self.bluesky, self.sync_status_manager)
        self.bluesky_to_mastodon_syncer = BlueskyToMastodonSyncer(self.mastodon, self.bluesky, self.sync_status_manager)

    def run(self):
        logging.info("开始同步过程")

        # 检查初始同步状态
        logging.info("检查初始同步状态")
        self.sync_status_manager.load_sync_status()

        # 同步 Mastodon 到 Bluesky
        logging.info("正在同步 Mastodon 到 Bluesky")
        self.mastodon_to_bluesky_syncer.sync()

        # 再次检查同步状态
        logging.info("Mastodon 到 Bluesky 同步后检查同步状态")
        self.sync_status_manager.load_sync_status()

        # 同步 Bluesky 到 Mastodon
        logging.info("正在同步 Bluesky 到 Mastodon")
        self.bluesky_to_mastodon_syncer.sync()

        logging.info("同步过程完成")

if __name__ == "__main__":
    sync_tool = SyncTool()
    sync_tool.run()
