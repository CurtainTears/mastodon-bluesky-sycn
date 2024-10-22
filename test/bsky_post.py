import json
from atproto import Client, models
from datetime import datetime

def get_bluesky_posts(username, password, limit=50):
    client = Client()
    client.login(username, password)

    data = client.get_author_feed(
                actor=client.me.did,
                filter='posts_no_replies',
                limit=limit
            )

    return data.feed

def save_posts_to_text(posts, filename='bsky2.txt'):
    with open(filename, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(str(post) + '\n\n')

if __name__ == "__main__":
    # 从环境变量或配置文件中获取这些值
    username = "asuka.today"
    password = "ehn4-tiks-lu7a-gld7"
    
    posts = get_bluesky_posts(username, password)
    
    save_posts_to_text(posts)
    print(f"已保存 {len(posts)} 条帖子到 bsky2.txt 文件中。")
