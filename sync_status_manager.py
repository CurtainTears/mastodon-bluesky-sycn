import json
import os
import logging

class SyncStatusManager:
    def __init__(self, filename='sync_status.json'):
        """
        初始化同步状态管理器
        :param filename: 存储同步状态的文件名
        """
        self.filename = filename
        self.sync_status = self.load_sync_status()

    def load_sync_status(self):
        """
        从文件加载同步状态
        :return: 同步状态列表
        """
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.sync_status = json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"无法加载 {self.filename}。创建新的同步状态。")
                self.sync_status = []
        else:
            self.sync_status = []
        return self.sync_status

    def save_sync_status(self):
        """
        将同步状态保存到文件
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.sync_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存同步状态失败: {str(e)}")

    def is_synced(self, post_id, direction):
        """
        检查帖子是否已同步
        :param post_id: 帖子ID
        :param direction: 同步方向 ('mastodon_to_bluesky' 或 'bluesky_to_mastodon')
        :return: 布尔值，表示是否已同步
        """
        if direction == 'mastodon_to_bluesky':
            return any(pair[0] == str(post_id) for pair in self.sync_status)
        elif direction == 'bluesky_to_mastodon':
            return any(pair[1] == str(post_id) for pair in self.sync_status)
        return False

    def mark_as_synced(self, post_id, synced_id, direction):
        """
        标记帖子为已同步
        :param post_id: 原始帖子ID
        :param synced_id: 同步后的帖子ID
        :param direction: 同步方向 ('mastodon_to_bluesky' 或 'bluesky_to_mastodon')
        """
        if direction == 'mastodon_to_bluesky':
            self.sync_status.append([str(post_id), str(synced_id)])
        elif direction == 'bluesky_to_mastodon':
            self.sync_status.append([str(synced_id), str(post_id)])
        self.save_sync_status()

    def get_sync_status(self):
        """
        获取当前的同步状态
        :return: 同步状态列表
        """
        return self.sync_status
