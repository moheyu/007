#!/usr/bin/env python3
import sys
import time
import logging
import subprocess
from pathlib import Path

# ---------- 配置 ----------
MARKER_FILE = Path("./output/.crawl_completed")   # 快照标记文件
BUILD_SCRIPT = Path("./rag/build_index.py")       # 索引构建脚本
CHECK_INTERVAL = 3                                # 检查间隔（秒）

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [快照监控] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_incremental():
    logger.info("🚀 检测到爬虫完成标记，开始增量索引...")
    try:
        logger.info(f"执行命令: {sys.executable} {BUILD_SCRIPT} --incremental")
        # 不捕获输出，以便实时查看执行过程
        logger.info("开始执行增量索引，实时输出如下:")
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "--incremental"]
        )
        logger.info(f"命令执行完成，返回码: {result.returncode}")
        if result.returncode == 0:
            logger.info("✅ 增量索引完成")
        else:
            logger.error(f"❌ 索引失败 (code={result.returncode})")
    except Exception as e:
        logger.error(f"❌ 执行异常: {e}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")

def main():
    logger.info(f"👀 监控标记文件: {MARKER_FILE}")
    while True:
        if MARKER_FILE.exists():
            run_incremental()
            MARKER_FILE.unlink()  # 删除标记，防止重复触发
            logger.info("🗑️ 标记文件已删除")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("监控已停止")