from dotenv import load_dotenv
load_dotenv()  # 加载环境变量

import os
import logging
import time
import json
from mastodon import Mastodon
from atproto import Client
from atproto_client.exceptions import InvokeTimeoutError
from mastodon_to_bluesky_sync import MastodonToBlueskySyncer
from bluesky_to_mastodon_sync import BlueskyToMastodonSyncer
from sync_status_manager import SyncStatusManager
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
        self.bluesky = Client()
        self.token_file = 'data/bluesky_token.json'
        self.initialize_bluesky_client()
        
        # 初始化同步状态管理器
        self.sync_status_manager = SyncStatusManager()
        # 初始化同步器mastodon到bluesky
        self.mastodon_to_bluesky_syncer = MastodonToBlueskySyncer(self.mastodon, self.bluesky, self.sync_status_manager)
        # 初始化同步器bluesky到mastodon
        self.bluesky_to_mastodon_syncer = BlueskyToMastodonSyncer(self.mastodon, self.bluesky, self.sync_status_manager)

    def save_token(self, token):
        with open(self.token_file, 'w') as f:
            json.dump({"token": token}, f)

    def load_token(self):
        try:
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                return data.get("token")
        except FileNotFoundError:
            return None

    def initialize_bluesky_client(self):
        token = self.load_token()
        
        if token:
            try:
                self.bluesky.login(None, None, token)
                logging.info("使用保存的令牌恢复Bluesky会话成功")
                return
            except Exception as e:
                logging.warning(f"使用保存的令牌恢复Bluesky会话失败: {str(e)}")

        self.login_bluesky()

    def login_bluesky(self):
        bluesky_username = os.environ.get('BLUESKY_USERNAME', '')
        bluesky_password = os.environ.get('BLUESKY_PASSWORD', '')
        logging.info(f"Bluesky用户名: {bluesky_username}")
        logging.info(f"Bluesky密码: {bluesky_password}")
        
        try:
            self.bluesky.login(bluesky_username, bluesky_password)
            token = self.bluesky.export_session_string()
            self.save_token(token)
            logging.info("Bluesky登录成功并保存新令牌")
            return
        except Exception as e:
            logging.warning(f"Bluesky登录失败：{str(e)}。") 
            raise

    def run(self):
        logging.info("开始同步过程")

        try:
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
        except Exception as e:
            logging.error(f"同步过程中出错: {str(e)}")
            if "invalid token" in str(e).lower():
                logging.info("令牌可能已失效，尝试重新登录")
                self.login_bluesky()
                # 可以在这里重新尝试失败的操作
                self.run()  # 重新运行同步过程

if __name__ == "__main__":
    sync_tool = SyncTool()
    sync_tool.run()
