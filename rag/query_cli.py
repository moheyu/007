#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
query_cli.py - 完整 RAG 命令行查询（使用 DashScope 官方集成）
"""

import os
import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.dashscope import DashScope
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from config import DASHSCOPE_API_KEY, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_PATH

# 1. 配置本地嵌入模型（与构建索引时一致）
Settings.embed_model = HuggingFaceEmbedding(
    model_name=str(EMBEDDING_MODEL_PATH),
    device="cpu"
)

# 2. 配置 LLM（使用 DashScope 官方集成，支持 qwen3.6-plus）
model_name = os.getenv("DASHSCOPE_MODEL", "qwen-max")

Settings.llm = DashScope(
    model_name=model_name,
    api_key=DASHSCOPE_API_KEY
)

# 3. 测试 LLM 连通性
print("正在测试 LLM 连通性...")
try:
    test_response = Settings.llm.complete("请回复：OK")
    print(f"LLM 测试成功，返回内容：'{test_response}'")
except Exception as e:
    print(f"LLM 测试失败，错误：{e}")
    sys.exit(1)

# 4. 加载已构建的向量库
db = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
collection = db.get_collection(CHROMA_COLLECTION_NAME)
vector_store = ChromaVectorStore(chroma_collection=collection)
index = VectorStoreIndex.from_vector_store(vector_store)

# 5. 自定义回答 Prompt（让回答更专业、简洁）
custom_prompt = PromptTemplate(
    "你是一个专业的Java技术知识库助手。请根据以下参考资料，用中文清晰、准确地回答用户的问题。\n"
    "参考资料：\n{context_str}\n"
    "问题：{query_str}\n"
    "回答："
)

# 6. 创建查询引擎
query_engine = index.as_query_engine(
    similarity_top_k=3,
    text_qa_template=custom_prompt
)

print("完整RAG知识库已加载，输入问题（输入 exit 退出）")

while True:
    q = input("\n问题：").strip()
    if q.lower() == "exit":
        break
    response = query_engine.query(q)
    print(f"\n回答：{response}\n")
    print("来源片段：")
    for node in response.source_nodes:
        title = node.metadata.get("title", "未知")
        url = node.metadata.get("url", "")
        score = node.score
        print(f"  - {title} | {url} | 相似度: {score:.3f}")