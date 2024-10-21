import os
import json
import logging
import re
import requests
from PIL import Image
import io
import time
from atproto import Client

class MastodonToBlueskySyncer:
    def __init__(self, mastodon_client, bluesky_client, sync_status_manager):
        # 初始化同步器，接收Mastodon和Bluesky的客户端以及同步状态管理器
        self.mastodon = mastodon_client
        self.bluesky = bluesky_client
        self.sync_status_manager = sync_status_manager
        self.toots_file = 'mastodon_toots.json'  # 用于保存Mastodon嘟文的文件

    def sync(self):
        try:
            # 获取Mastodon账户信息
            account = self.mastodon.account_verify_credentials()
            # 获取最近的10条Mastodon嘟文
            mastodon_posts = self.mastodon.account_statuses(account.id, limit=20)
            logging.info(f"从Mastodon用户 {account.username} 获取了 {len(mastodon_posts)} 条嘟文")
            
            synced_count = 0
            skipped_count = 0
            for post in mastodon_posts:
                # 记录每条嘟文的基本信息
                logging.info(f"正在处理Mastodon嘟文 {post.id}:")
                logging.info(f"  内容: {post.content[:100]}...")
                logging.info(f"  创建时间: {post.created_at}")
                logging.info(f"  URL: {post.url}")
                logging.info(f"  媒体附件数: {len(post.media_attachments)}")
                
                self.save_toot(post)  # 保存嘟文到本地文件
                
                # 跳过回复、转发、提及或包含链接的嘟文
                if post.in_reply_to_id is not None or post.reblog is not None or post.mentions or '@' in post.content or post.visibility != 'public':
                    logging.info(f"跳过Mastodon嘟文 {post.id} (回复、转发、提及或非公开)")
                    skipped_count += 1
                    continue
                
                # 如果嘟文未同步，则进行同步
                if not self.sync_status_manager.is_synced(post.id, 'mastodon_to_bluesky'):
                    bluesky_post = self.convert_mastodon_to_bluesky(post)
                    logging.info(f"正在同步Mastodon嘟文 {post.id} 到Bluesky")
                    logging.info(f"Bluesky帖子内容: {bluesky_post}")
                    create_response = self.bluesky.com.atproto.repo.create_record({
                        'repo': self.bluesky.me.did,
                        'collection': 'app.bsky.feed.post',
                        'record': bluesky_post
                    })
                    logging.info(f"Bluesky创建记录响应: {create_response}")
                    self.sync_status_manager.mark_as_synced(post.id, create_response.cid, 'mastodon_to_bluesky')
                    logging.info(f"成功同步Mastodon嘟文 {post.id} 到Bluesky")
                    synced_count += 1
                else:
                    logging.info(f"Mastodon嘟文 {post.id} 已同步，跳过")
                    skipped_count += 1
            
            logging.info(f"Mastodon同步摘要: 同步了 {synced_count} 条嘟文, 跳过了 {skipped_count} 条嘟文")
        except Exception as e:
            logging.error(f"同步Mastodon到Bluesky时出错: {str(e)}")
            logging.exception("异常详情:")

    def save_toot(self, toot):
        # 保存Mastodon嘟文到本地JSON文件
        try:
            toots = []
            if os.path.exists(self.toots_file):
                with open(self.toots_file, 'r', encoding='utf-8') as f:
                    toots = json.load(f)
            
            toot_data = {
                'id': toot.id,
                'created_at': toot.created_at.isoformat(),
                'content': toot.content,
                'url': toot.url,
                'media_attachments': [
                    {'type': m.type, 'url': m.url} for m in toot.media_attachments
                ],
                'language': toot.language,
            }
            toots.append(toot_data)
            
            with open(self.toots_file, 'w', encoding='utf-8') as f:
                json.dump(toots, f, ensure_ascii=False, indent=2)
            
            logging.info(f"保存了详细的嘟文 {toot.id} 到 {self.toots_file}")
        except Exception as e:
            logging.error(f"保存嘟文 {toot.id} 到文件时出错: {str(e)}")

    def compress_image(self, image_data, max_size_kb=950):
        # 压缩图片，同时清除元数据
        img = Image.open(io.BytesIO(image_data))
        
        # 清除元数据
        data = list(img.getdata())
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(data)

        if img_without_exif.mode != 'RGB':
            img_without_exif = img_without_exif.convert('RGB')
        
        quality = 95
        while True:
            buffer = io.BytesIO()
            img_without_exif.save(buffer, format="JPEG", quality=quality)
            size = buffer.getbuffer().nbytes
            if size <= max_size_kb * 1024 or quality <= 20:
                logging.info(f"压缩后的图片大小: {size} 字节, 质量: {quality}")
                return buffer.getvalue()
            quality -= 5
            logging.info(f"图片仍然过大 ({size} 字节), 降低质量至 {quality}")

    def download_image(self, image_url):
        # 从URL下载图片
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                return response.content
            else:
                logging.error(f"下载图片失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"下载图片时出错: {str(e)}")
            return None

    def upload_image_to_bluesky(self, image_data, max_retries=5, timeout=30):
        # 上传图片到Bluesky，包含重试机制
        for attempt in range(max_retries):
            try:
                logging.info(f"第 {attempt + 1} 次尝试上传图片到Bluesky")
                upload_response = self.bluesky.com.atproto.repo.upload_blob(image_data, timeout=timeout)
                if hasattr(upload_response, 'blob'):
                    logging.info(f"成功上传图片，blob: {upload_response.blob}")
                    return upload_response.blob
                else:
                    logging.error(f"上传响应不包含blob: {upload_response}")
            except Exception as e:
                logging.error(f"上传图片到Bluesky时出错: {str(e)}")
                logging.exception("异常详情:")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logging.info(f"等待 {wait_time} 秒后进行下一次尝试")
                time.sleep(wait_time)
        logging.error(f"经过 {max_retries} 次尝试后仍未能上传图片")
        return None

    def process_and_upload_image(self, image_url):
        # 处理并上传图片的完整流程
        image_data = self.download_image(image_url)
        if image_data is None:
            return None

        logging.info(f"成功下载图片，大小: {len(image_data)} 字节")

        compressed_image = self.compress_image(image_data)
        compressed_size = len(compressed_image)
        logging.info(f"压缩后的图片大小: {compressed_size} 字节")

        if compressed_size > 976.56 * 1024:
            logging.error(f"压缩后的图片仍然过大: {compressed_size} 字节")
            return None

        return self.upload_image_to_bluesky(compressed_image)

    def convert_mastodon_to_bluesky(self, mastodon_post):
        # 将Mastodon嘟文转换为Bluesky帖子格式
        text = re.sub('<[^<]+?>', '', mastodon_post.content)  # 移除HTML标签
        #检查字数是否超过250字
        if len(text) > 250:
            text = text[:250] + '...'
        
        text = text + '\nfrom mastodon @asuka@mastodon.asuka.today'

        bluesky_post = {
            '$type': 'app.bsky.feed.post',
            'text': text,
            'createdAt': mastodon_post.created_at.isoformat(),
            'langs': [mastodon_post.language] if mastodon_post.language else []
        }

        # 处理图片附件
        if mastodon_post.media_attachments:
            images = []
            for attachment in mastodon_post.media_attachments:
                if attachment.type == 'image':
                    blob = self.process_and_upload_image(attachment.url)
                    if blob:
                        images.append({
                            'alt': attachment.description or '',
                            'image': blob
                        })
            if images:
                bluesky_post['embed'] = {
                    '$type': 'app.bsky.embed.images',
                    'images': images
                }

        return bluesky_post
