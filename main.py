import time
import logging
import os
from sync_tool import SyncTool

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从环境变量获取睡眠间隔，默认为300秒（5分钟）
SLEEP_INTERVAL = int(os.environ.get('SYNC_INTERVAL', 300))

def run_sync():
    try:
        sync_tool = SyncTool()
        sync_tool.run()
        logging.info("同步执行成功")
    except Exception as e:
        logging.error(f"同步执行失败: {str(e)}")

def main():
    while True:
        logging.info("开始执行同步")
        run_sync()
        logging.info(f"同步完成，等待 {SLEEP_INTERVAL} 秒后再次执行")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
