import json
import dashscope
from http import HTTPStatus
from config import DASHSCOPE_API_KEY, AI_MAX_TOKEN

dashscope.api_key = DASHSCOPE_API_KEY

def ai_summary(text: str):
    if not DASHSCOPE_API_KEY or not text:
        return text
    
    # ✅ 智能截断（替代硬编码）
    text = text[:AI_MAX_TOKEN]
    print(f"[AI处理] 文本长度：{len(text)}字符")

    try:
        # AI摘要调用
        response = dashscope.Generation.call(
            model="qwen-turbo",
            prompt=f"为以下内容生成简洁知识库摘要：{text}"
        )
        if response.status_code == HTTPStatus.OK:
            result = response.output.text
            # ✅ Token统计（个人控制成本）
            print(f"[AI完成] 消耗Token：{response.usage.total_tokens}")
            return result
        return text
    
    # ✅ JSON/AI错误容错，绝不崩溃
    except Exception as e:
        print(f"[AI降级] 调用失败，使用原始文本：{str(e)}")
        return text

# 保持向后兼容的函数
def ai_filter_and_summarize(text, api_config):
    if not api_config.get('api_key'):
        return text
    return ai_summary(text)

def generate_metadata(text, url, api_config):
    if not api_config.get('api_key'):
        return {
            "title": "未命名",
            "keywords": [],
            "description": "",
            "url": url,
            "created_at": ""
        }
    
    summary = ai_summary(text)
    return {
        "title": url,
        "keywords": [],
        "description": summary[:100] + "..." if len(summary) > 100 else summary,
        "url": url,
        "created_at": ""
    }