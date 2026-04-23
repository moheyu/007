import os
from dotenv import load_dotenv

# 加载环境变量（兼容无.env文件）
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ====================== 【个人专属可配置项】======================
# 1. AI配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
AI_MAX_TOKEN = 8000  # AI处理长度（可自行调整）

# 2. 爬取基础配置
REQUEST_DELAY = 2  # 请求间隔秒数（保护你的IP，不用改）
MAX_RETRY = 3  # 失败重试次数
RETRY_STATUS_CODES = {403, 429, 500, 502, 503}  # 全场景重试

# 3. 内容爬取规则（✅ 改这里就能适配不同网站，不用动代码）
CONTENT_PATTERNS = [r"/article/", r"/blog/", r"/docs/", r"/post/"]
EXCLUDE_PATTERNS = [r"/tag/", r"/category/", r"/archive/", r"/page/\d+"]

# 4. 本地存储配置
SAVE_PROGRESS_INTERVAL = 1  # ✅ 每成功1页就存进度（绝不丢数据）
# =================================================================

# 启动校验（个人使用防手误）
def check_config():
    if not DASHSCOPE_API_KEY:
        print("[警告] 未配置DASHSCOPE_API_KEY，将跳过AI摘要生成")
    print("[配置] 加载完成，规则/存储/重试已生效")

check_config()

# 输出目录配置（保持向后兼容）
OUTPUT_DIR = "./output"
OUTPUT_DIR_JSON = "./output/json"
OUTPUT_DIR_MARKDOWN = "./output/markdown"
OUTPUT_DIR_JSON_V4 = "./output/json"
PROGRESS_FILE = "./output/crawl_progress.json"
SUMMARY_FILE = "./output/crawl_summary.json"

# 爬虫配置（保持向后兼容）
CRAWL_CONFIG = {
    "max_depth": 2,
    "max_pages": 50,
    "request_delay": REQUEST_DELAY,
    "request_timeout": 30,
    "respect_robots_txt": True,
    "user_agent": "Mozilla/5.0 (compatible; MySiteArchiver/1.0; +http://example.com/bot)",
    "content_path_patterns": CONTENT_PATTERNS,
    "exclude_path_patterns": EXCLUDE_PATTERNS,
    "progress_save_interval": SAVE_PROGRESS_INTERVAL,
    "retry_count": MAX_RETRY,
    "retry_backoff": 2.0
}

# 基础URL配置（保持向后兼容）
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "qwen3.6-plus"

# ====================== RAG 知识库配置 ======================
import os
from pathlib import Path

# 项目根目录（自动计算，无需修改）
BASE_DIR = Path(__file__).parent

# 向量数据库配置
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = "javaguide_kb"

# 本地嵌入模型路径（优先读取环境变量，否则使用默认值）
# 如果你在其他电脑上使用，只需在 .env 中设置 EMBEDDING_MODEL_PATH 即可
EMBEDDING_MODEL_PATH = os.getenv(
    "EMBEDDING_MODEL_PATH",
    str(BASE_DIR / "models" / "bge-small-zh-v1.5")  # 建议把模型复制到项目内
)

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"