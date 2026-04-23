#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py - 构建向量索引

遍历 output/json/ 目录下的所有 JSON 文件，将内容向量化并存储到 ChromaDB。
"""

import os
import sys
import json
from pathlib import Path
from tqdm import tqdm

# 添加父目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from config import DASHSCOPE_API_KEY, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_PATH

# 配置嵌入模型
if not DASHSCOPE_API_KEY:
    raise ValueError("请在 .env 文件中配置 DASHSCOPE_API_KEY")



Settings.embed_model = HuggingFaceEmbedding(
    model_name=str(EMBEDDING_MODEL_PATH),
    device="cpu"
)
# 配置
JSON_DIR = Path("./output/json")
CHROMA_DB_DIR = CHROMA_DB_PATH
COLLECTION_NAME = CHROMA_COLLECTION_NAME
MIN_CONTENT_LENGTH = 100


def load_documents():
    """加载 JSON 文件并转换为 Document 对象"""
    documents = []
    json_files = list(JSON_DIR.rglob("*.json"))
    
    if not json_files:
        print(f"未找到 JSON 文件：{JSON_DIR}")
        return documents
    
    print(f"找到 {len(json_files)} 个 JSON 文件")
    
    for json_file in tqdm(json_files, desc="加载文档"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 提取内容和元数据
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            
            # 过滤短内容
            if len(content) < MIN_CONTENT_LENGTH:
                continue
            
            # 构建元数据
            doc_metadata = {
                "title": metadata.get("title", str(json_file.name)),
                "url": metadata.get("url", ""),
                "source": str(json_file)
            }
            
            # 创建 Document 对象
            document = Document(
                text=content,
                metadata=doc_metadata
            )
            documents.append(document)
            
        except Exception as e:
            print(f"处理文件失败 {json_file}: {e}")
            continue
    
    print(f"成功加载 {len(documents)} 个文档")
    return documents


def build_index(documents):
    """构建向量索引（修正版）"""
    if not documents:
        print("没有文档可索引")
        return

    # 1. 创建 ChromaDB 客户端
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # 2. 删除旧集合（确保从头构建，避免残留）
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"已删除旧集合: {COLLECTION_NAME}")
    except Exception:
        pass

    # 3. 创建新集合
    collection = client.create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # 4. 显式创建存储上下文
    from llama_index.core.storage.storage_context import StorageContext
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("开始构建索引...")
    print(f"文档数量: {len(documents)}")
    print(f"存储目录: {CHROMA_DB_DIR}")

    # 5. 构建索引时传入 storage_context
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    # 6. 验证写入结果
    doc_count = collection.count()
    print(f"\n写入后集合中文档数量: {doc_count}")
    print(f"向量库已保存到: {CHROMA_DB_DIR}")
    print(f"集合名称: {COLLECTION_NAME}")

    if doc_count == 0:
        print("⚠️ 警告：向量库中没有任何文档，请检查数据或嵌入模型配置。")


if __name__ == "__main__":
    print("=== RAG 向量索引构建 ===")
    print(f"JSON 目录: {JSON_DIR}")
    print(f"ChromaDB 目录: {CHROMA_DB_DIR}")
    print()

    documents = load_documents()
    build_index(documents)