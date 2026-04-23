import requests
from requests.exceptions import HTTPError
from config import REQUEST_DELAY, MAX_RETRY, RETRY_STATUS_CODES
import time

# 线程安全（个人单线程够用）
_session = requests.Session()

def fetch_webpage(url: str, timeout=15):
    retry = 0
    while retry < MAX_RETRY:
        try:
            # 固定请求头，统一规范
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = _session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return response.content
        
        except HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            # 仅重试配置中的状态码
            if status_code in RETRY_STATUS_CODES:
                retry += 1
                print(f"[重试] {url} 失败{retry}次，状态码：{status_code}")
                time.sleep(2 * retry)
                continue
            print(f"[请求失败] {url} 状态码：{status_code}")
            return None
        
        except Exception as e:
            retry += 1
            print(f"[网络异常] {url} 错误：{str(e)}")
            time.sleep(2)
            continue

# ✅ 新增：爬取结束关闭session（解决资源泄漏）
def close_session():
    _session.close()

# 保持向后兼容的函数
def get_session():
    return _session