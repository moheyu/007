from openai import OpenAI
from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL
)

response = client.chat.completions.create(
    model=DASHSCOPE_MODEL,
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "请介绍一下你自己。"}
    ]
)

print("API 连接测试成功！")
print(f"模型：{DASHSCOPE_MODEL}")
print(f"回复：{response.choices[0].message.content}")
