import trafilatura
from bs4 import BeautifulSoup
import requests
import re
from config import CONTENT_PATTERNS, EXCLUDE_PATTERNS

# 顶部统一导入（修复原问题）
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ✅ 新增：提取降级逻辑（个人爬小众网站必备）
def extract_content(url: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        # 1. 优先用trafilatura精准提取
        content = trafilatura.extract(resp.content)
        if content:
            return content
        
        # 2. ❌ 提取失败 → BS4兜底（抓article/main标签）
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup.find_all(["article", "main"]):
            return tag.get_text(strip=True, separator="\n")
        
        print(f"[提取失败] {url} 无正文内容")
        return None
    except:
        return None

# ✅ 精准判断内容页（正则统一，不误判）
def is_content_url(url: str):
    # 排除规则优先
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, url):
            return False
    # 匹配内容规则
    for pattern in CONTENT_PATTERNS:
        if re.search(pattern, url):
            return True
    return False

# 保持向后兼容的函数
def discover_links(html: str, base_url: str, content_patterns: list = None, exclude_patterns: list = None, same_domain_only: bool = True) -> list:
    from urllib.parse import urljoin, urlparse
    
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = set()
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        if same_domain_only and parsed.netloc != base_domain:
            continue
        
        if parsed.scheme not in ["http", "https"]:
            continue
        
        if exclude_patterns:
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern.startswith("^") or pattern.endswith("$"):
                    if re.search(pattern, parsed.path + ("?" if parsed.query else "") + parsed.query):
                        should_exclude = True
                        break
                else:
                    if pattern in (parsed.path + ("?" if parsed.query else "") + parsed.query):
                        should_exclude = True
                        break
            if should_exclude:
                continue
        
        if content_patterns:
            is_content = False
            for pattern in content_patterns:
                if pattern.startswith("^") or pattern.endswith("$"):
                    if re.search(pattern, parsed.path):
                        is_content = True
                        break
                else:
                    if pattern in parsed.path:
                        is_content = True
                        break
            if not is_content:
                continue
        
        links.add(full_url)
    
    return list(links)

# 保持向后兼容的函数
def normalize_url(url: str) -> str:
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)
    parsed = parsed._replace(fragment='')
    path = parsed.path.rstrip('/')
    parsed = parsed._replace(path=path)
    return urlunparse(parsed)