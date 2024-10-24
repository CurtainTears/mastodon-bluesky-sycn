from dotenv import load_dotenv
load_dotenv()  # 加载环境变量

import os
import json
import logging
import requests
from PIL import Image
import io

class BlueskyToMastodonSyncer:
    def __init__(self, mastodon_client, bluesky_client, sync_status_manager):
        # 初始化同步器，接收Mastodon和Bluesky的客户端以及同步状态管理器
        self.mastodon = mastodon_client
        self.bluesky = bluesky_client
        self.sync_status_manager = sync_status_manager
        self.posts_file = 'bluesky_posts.json'  # 用于保存Bluesky帖子的文件

    def sync(self):
        try:
            # 获取Bluesky用户的帖子
            data = self.bluesky.get_author_feed(
                actor=self.bluesky.me.did,
                filter='posts_no_replies',
                limit=30
            )
            bluesky_posts = data.feed
            logging.info(f"从Bluesky获取了 {len(bluesky_posts)} 条帖子")
            
            synced_count = 0
            skipped_count = 0
            for post in bluesky_posts:
                post_view = post.post
                # 更安全的检查方式
                has_embed_record = (hasattr(post_view, 'record') and 
                                    hasattr(post_view.record, 'embed') and 
                                    post_view.record.embed is not None and 
                                    hasattr(post_view.record.embed, 'record') and 
                                    post_view.record.embed.record is not None)
                has_reason = hasattr(post_view, 'reason') and post_view.reason is not None

                if has_embed_record or has_reason:
                    logging.info(f"跳过Bluesky帖子 {post_view.cid} (包含提及或转发)")
                    skipped_count += 1
                    continue
                
                logging.info(f"正在处理Bluesky帖子 {post_view.cid}:")
                logging.info(f"  内容: {post_view.record.text[:100]}...")
                
                # self.save_post(post_view)  # 保存帖子到本地文件
                
                # 如果帖子未同步，则进行同步
                if not self.sync_status_manager.is_synced(post_view.cid, 'bluesky_to_mastodon'):
                    mastodon_post, media_ids = self.convert_bluesky_to_mastodon(post_view)
                    response = self.mastodon.status_post(mastodon_post, media_ids=media_ids)
                    self.sync_status_manager.mark_as_synced(post_view.cid, response['id'], 'bluesky_to_mastodon')
                    logging.info(f"成功将Bluesky帖子 {post_view.cid} 同步到Mastodon")
                    synced_count += 1
                else:
                    logging.info(f"Bluesky帖子 {post_view.cid} 已同步，跳过")
                    skipped_count += 1
            
            logging.info(f"Bluesky同步摘要: 同步了 {synced_count} 条帖子, 跳过了 {skipped_count} 条帖子")
        except Exception as e:
            logging.error(f"同步Bluesky到Mastodon时出错: {str(e)}")
            logging.exception("异常详情:")

    def save_post(self, post):
        # 保存Bluesky帖子到本地JSON文件
        try:
            posts = []
            if os.path.exists(self.posts_file):
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    posts = json.load(f)
            
            post_data = {
                'cid': post.cid,
                'uri': post.uri,
                'text': post.record.text,
                'created_at': post.record.created_at,
                'embed': post.embed.dict() if hasattr(post, 'embed') else None
            }
            posts.append(post_data)
            
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            
            logging.info(f"已将Bluesky帖子 {post.cid} 保存到 {self.posts_file}")
            logging.info(f"已保存的帖子总数: {len(posts)}")
        except Exception as e:
            logging.error(f"保存Bluesky帖子 {post.cid} 时出错: {str(e)}")
            logging.exception("异常详情:")

    def convert_bluesky_to_mastodon(self, bluesky_post):
        # 将Bluesky帖子转换为Mastodon格式
        from_bluesky_at = os.environ.get('FROM_BLUESKY_AT', '')

        if from_bluesky_at:
            text = bluesky_post.record.text + '\n\nfrom bluesky ' + from_bluesky_at
        else:
            text = bluesky_post.record.text
        
        media_ids = []

        # 处理帖子中的图片
        if hasattr(bluesky_post.embed, 'images'):
            logging.info(f"Bluesky帖子 {bluesky_post.cid} 包含图片，尝试上传")
            for image in bluesky_post.embed.images:
                image_url = image.fullsize
                alt_text = image.alt or ''
                logging.info(f"正在从URL上传图片: {image_url}")
                media_id = self.upload_image_to_mastodon(image_url, alt_text)
                if media_id:
                    media_ids.append(media_id)
                    logging.info(f"成功上传图片到Mastodon，media_id: {media_id}")
                else:
                    logging.warning(f"从URL上传图片失败: {image_url}")

        logging.info(f"已将Bluesky帖子转换为Mastodon帖子。文本: {text[:100]}..., 媒体ID: {media_ids}")
        return text, media_ids

    def upload_image_to_mastodon(self, image_url, alt_text=''):
        # 上传图片到Mastodon
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = response.content
                media = self.mastodon.media_post(image_data, mime_type='image/jpeg', description=alt_text)
                logging.info(f"成功上传图片到Mastodon，media_id: {media['id']}")
                return media['id']
            else:
                logging.error(f"从Bluesky下载图片失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"上传图片到Mastodon时出错: {str(e)}")
            logging.exception("异常详情:")
            return None
