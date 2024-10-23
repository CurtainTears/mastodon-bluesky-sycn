from .base_platform import BasePlatform
from atproto import Client
import os
import logging
import json

class BlueskyPlatform(BasePlatform):
    def __init__(self):
        self.instance_url = os.environ.get('BLUESKY_INSTANCE_URL', '')
        self.username = os.environ.get('BLUESKY_USERNAME', '')
        self.password = os.environ.get('BLUESKY_PASSWORD', '')
        self.token_file = 'data/bluesky_token.json'
        self.client = Client(self.instance_url) if self.instance_url else Client()
        self.get_post_limit = int(os.environ.get('BLUESKY_GET_POST_LIMIT', 20))

    def login(self):
        token = self.load_token()
        
        if token:
            try:
                self.client.login(None, None, token)
                logging.info("使用保存的令牌恢复Bluesky会话成功")
                return
            except Exception as e:
                logging.warning(f"使用保存的令牌恢复Bluesky会话失败: {str(e)}")

        try:
            self.client.login(self.username, self.password)
            token = self.client.export_session_string()
            self.save_token(token)
            logging.info("Bluesky登录成功并保存新令牌")
        except Exception as e:
            logging.error(f"Bluesky 登录失败: {str(e)}")
            raise

    def send_post(self, content, media_ids=None):
        if not self.client:
            raise Exception("Bluesky 客户端未初始化，请先登录")
        
        try:
            images = []
            if media_ids:
                for media_id in media_ids:
                    images.append({"image": media_id, "alt": "Image"})
            
            response = self.client.send_post(text=content, images=images)
            return response
        except Exception as e:
            logging.error(f"发布 Bluesky 帖子失败: {str(e)}")
            raise

    def get_post(self):
        if not self.client:
            raise Exception("Bluesky 客户端未初始化，请先登录")
        
        try:
            profile = self.client.get_profile(self.client.me.did)
            feed = self.client.get_author_feed(profile.did, limit=self.get_post_limit)
            return feed.feed
        except Exception as e:
            logging.error(f"获取 Bluesky 帖子失败: {str(e)}")
            raise

    def upload_media(self, media_file):
        if not self.client:
            raise Exception("Bluesky 客户端未初始化，请先登录")
        
        try:
            with open(media_file, 'rb') as f:
                upload = self.client.upload_blob(f.read())
            return upload.blob.ref.link
        except Exception as e:
            logging.error(f"上传 Bluesky 媒体失败: {str(e)}")
            raise

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
