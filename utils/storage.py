import os
import json
import hashlib
from urllib.parse import urlparse
from datetime import datetime

# 个人专属存储路径
BASE_OUTPUT = "./output"
PROGRESS_FILE = "./progress.json"

# ✅ 按域名分目录 + 可读文件名（核心优化）
def get_save_path(url):
    domain = urlparse(url).netloc
    # 目录：output/markdown/域名/
    dir_path = os.path.join(BASE_OUTPUT, "markdown", domain)
    os.makedirs(dir_path, exist_ok=True)
    
    # 文件名：域名_哈希.md（简洁不重复，个人够用）
    hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{domain.replace('.', '_')}_{hash_name}.md"
    return os.path.join(dir_path, filename)

# ✅ 保存内容（编码容错，不崩）
def save_content(url, content):
    if not content:
        return
    file_path = get_save_path(url)
    with open(file_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"# {url}\n\n{content}")
    print(f"[保存] {file_path}")

# 进度保存/加载 + 自动清理临时文件
def save_progress(visited, domain, max_depth):
    data = {"visited": list(visited), "domain": domain, "max_depth": max_depth}
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    
    # ✅ 自动清理临时文件
    for f in os.listdir("."):
        if f.endswith(".tmp"):
            os.remove(f)

def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return None
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 保持向后兼容的函数
def ensure_dirs(markdown_dir: str, json_dir: str):
    os.makedirs(markdown_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

def generate_filename(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_").replace(":", "_")
    path_hash = hashlib.md5(parsed.path.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{domain}_{path_hash}"

def save_page(content: str, metadata: dict, url: str, markdown_dir: str, json_dir: str) -> tuple:
    ensure_dirs(markdown_dir, json_dir)
    filename_base = generate_filename(url)
    md_file = os.path.join(markdown_dir, f"{filename_base}.md")
    json_file = os.path.join(json_dir, f"{filename_base}.json")
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# {metadata.get('title', '未命名')}\n\n")
        f.write(f"URL: {url}\n\n")
        f.write(content)
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "content": content,
            "metadata": metadata
        }, f, ensure_ascii=False, indent=2)
    
    return str(md_file), str(json_file)

def save_progress_compat(progress_file: str, data: dict):
    progress_dir = os.path.dirname(progress_file)
    if progress_dir:
        os.makedirs(progress_dir, exist_ok=True)
    
    temp_file = progress_file + ".tmp"
    
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    os.replace(temp_file, progress_file)

def load_progress_compat(progress_file: str) -> dict:
    if not os.path.exists(progress_file):
        return {"start_url": "", "visited": [], "last_update": ""}
    
    with open(progress_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data

def save_summary(summary_file: str, summary_data: dict):
    summary_dir = os.path.dirname(summary_file)
    if summary_dir:
        os.makedirs(summary_dir, exist_ok=True)
    
    temp_file = summary_file + ".tmp"
    
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    os.replace(temp_file, summary_file)