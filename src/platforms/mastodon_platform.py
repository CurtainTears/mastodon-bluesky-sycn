from .base_platform import BasePlatform
from mastodon import Mastodon
import os
import logging

class MastodonPlatform(BasePlatform):
    def __init__(self):
        self.instance_url = os.environ.get('MASTODON_INSTANCE_URL', '')
        if not self.instance_url.startswith('http'):
            self.instance_url = f'https://{self.instance_url}'
        
        self.access_token = os.environ.get('MASTODON_ACCESS_TOKEN')
        self.get_post_limit = os.environ.get('MASTODON_GET_POST_LIMIT', 20)
        self.client = None
        self.account = None

    def login(self):
        try:
            self.client = Mastodon(
                access_token=self.access_token,
                api_base_url=self.instance_url
            )
            # 验证凭据
            self.account = self.client.account_verify_credentials()
            logging.info("Mastodon 登录成功")
        except Exception as e:
            logging.error(f"Mastodon 登录失败: {str(e)}")
            raise

    def send_post(self, content, media_ids=None, sensitive=False, visibility='public', spoiler_text=None):
        if not self.client:
            raise Exception("Mastodon 客户端未初始化，请先登录")
        
        try:
            status = self.client.status_post(
                status=content,
                media_ids=media_ids,
                sensitive=sensitive,
                visibility=visibility,
                spoiler_text=spoiler_text
            )
            return status
        except Exception as e:
            logging.error(f"发布 Mastodon 帖子失败: {str(e)}")
            raise

    def get_post(self):
        if not self.client:
            raise Exception("Mastodon 客户端未初始化，请先登录")
        
        try:
            status = self.client.account_statuses(self.account.id, self.get_post_limit)
            return status
        except Exception as e:
            logging.error(f"获取 Mastodon 帖子失败: {str(e)}")
            raise

    def upload_media(self, media_file, description=None):
        if not self.client:
            raise Exception("Mastodon 客户端未初始化，请先登录")
        
        try:
            media = self.client.media_post(media_file, description=description)
            return media['id']
        except Exception as e:
            logging.error(f"上传 Mastodon 媒体失败: {str(e)}")
            raise