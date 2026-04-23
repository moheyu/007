from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

_robots_cache = {}

def can_fetch(url: str, user_agent: str = "*", respect_robots: bool = True) -> bool:
    if not respect_robots:
        return True
    
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    if base in _robots_cache:
        rp = _robots_cache[base]
    else:
        rp = RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            rp.read()
            _robots_cache[base] = rp
        except Exception as e:
            logger.warning(f"无法获取 {base}/robots.txt: {e}")
            return True
    
    return rp.can_fetch(user_agent, url)
