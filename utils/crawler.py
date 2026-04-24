from urllib.parse import urlparse, urljoin
from utils.extractor import extract_content, discover_links, is_content_url
from utils.storage import save_content, save_progress, load_progress
from utils.fetcher import fetch_webpage
from config import SAVE_PROGRESS_INTERVAL
import hashlib

# 全局状态
visited_urls = set()
queue = []
crawled_pages = 0
MAX_PAGES = 100  # 单次爬取最大页面数

# ✅ 核心：URL规范化（彻底去重）
def normalize_url(base_url, link):
    parsed = urljoin(base_url, link)
    return parsed.split("#")[0].strip("/")  # 去掉锚点+统一尾部斜杠

# ✅ 核心：每次成功爬取就存进度
def crawl_page(url, domain, max_depth, current_depth=0):
    global crawled_pages
    if current_depth > max_depth or url in visited_urls or crawled_pages >= MAX_PAGES:
        return
    visited_urls.add(url)
    crawled_pages += 1

    print(f"[爬取] {url} 深度：{current_depth}")
    content = extract_content(url)
    if not content:
        # 保存失败 URL
        with open("failed_urls.txt", "a", encoding="utf-8") as f:
            f.write(f"{url}\n")
        return

    # 保存内容 + 立即保存进度
    save_content(url, content)
    if len(visited_urls) % SAVE_PROGRESS_INTERVAL == 0:
        save_progress(visited_urls, domain, max_depth)

    # 递归爬取子链接
    try:
        html = fetch_webpage(url)
        if html:
            links = discover_links(html, url)
            for link in links:
                norm_link = normalize_url(url, link)
                if norm_link not in visited_urls:
                    crawl_page(norm_link, domain, max_depth, current_depth + 1)
    except Exception as e:
        print(f"[链接发现失败] {url} 错误：{str(e)}")

# ✅ 续爬：自动读取历史配置，支持指定续爬 URL
def resume_crawl(url=None):
    progress = load_progress()
    if not progress:
        print("[错误] 无进度文件，无法续爬")
        return
    global visited_urls, crawled_pages
    visited_urls = set(progress.get("visited", []))
    crawled_pages = 0  # 重置计数器，确保续爬时不超过100页
    
    # 如果提供了 URL，使用它作为续爬起点；否则使用进度文件中的域名
    if url:
        domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        print(f"[续爬] 指定根域名：{domain}，深度：{progress['max_depth']}，已爬：{len(visited_urls)}页，本次续爬最多再爬{MAX_PAGES}页")
        crawl_page(url, domain, progress["max_depth"])
    else:
        domain = progress["domain"]
        max_depth = progress["max_depth"]
        print(f"[续爬] 域名：{domain}，深度：{max_depth}，已爬：{len(visited_urls)}页，本次续爬最多再爬{MAX_PAGES}页")
        crawl_page(domain, domain, max_depth)

# 保持向后兼容的函数
def process_single_url(url, mode, config, api_config):
    try:
        content = extract_content(url)
        if not content:
            return {"success": False, "error": "未能提取到网页内容"}
        
        from utils.ai_worker import ai_filter_and_summarize, generate_metadata
        from utils.storage import save_page
        
        if mode == "process" and api_config.get("api_key"):
            content = ai_filter_and_summarize(content, api_config)
            metadata = generate_metadata(content, url, api_config)
        else:
            metadata = {"title": url, "keywords": [], "description": ""}
        
        md_file, json_file = save_page(
            content, metadata, url, 
            config["markdown_dir"], config["json_dir"]
        )
        return {"success": True, "json_file": json_file}
    except Exception as e:
        return {"success": False, "error": str(e)}

def crawl_site(start_url, mode="process", 
               max_depth=2, max_pages=50,
               request_delay=2.0, respect_robots=True,
               progress_file=None, summary_file=None,
               api_config=None, output_dirs=None):
    # 保持向后兼容，调用新的爬取逻辑
    domain = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
    print(f"[开始] 爬取域名：{domain}，深度：{max_depth}")
    global visited_urls, crawled_pages
    visited_urls = set()
    crawled_pages = 0  # 重置计数器，确保不超过100页
    crawl_page(start_url, domain, max_depth)
    print("[完成] 爬取结束，已自动保存进度+清理临时文件")