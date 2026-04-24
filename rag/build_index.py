#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py - 构建向量索引

遍历 output/json/ 目录下的所有 JSON 文件，将内容向量化并存储到 ChromaDB。
"""

import os
import sys
import json
import hashlib
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

# URL 记录文件（用于增量去重）
INDEXED_URLS_FILE = CHROMA_DB_DIR / "indexed_urls.json"


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

            # 获取 URL 并生成唯一 ID
            url = metadata.get("url", "")
            doc_id = hashlib.md5(url.encode('utf-8')).hexdigest()

            # 构建元数据
            doc_metadata = {
                "title": metadata.get("title", str(json_file.name)),
                "url": url,
                "source": str(json_file)
            }

            # 创建 Document 对象（显式传递 doc_id）
            document = Document(
                text=content,
                metadata=doc_metadata,
                doc_id=doc_id
            )
            documents.append(document)
            
        except Exception as e:
            print(f"处理文件失败 {json_file}: {e}")
            continue
    
    print(f"成功加载 {len(documents)} 个文档")
    return documents


def save_indexed_urls(documents):
    """保存已索引的 URL 到记录文件"""
    urls = [doc.metadata["url"] for doc in documents if doc.metadata.get("url")]
    urls = list(set(urls))  # 去重
    
    # 确保目录存在
    INDEXED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(INDEXED_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(urls)} 条 URL 到索引记录: {INDEXED_URLS_FILE}")


def load_incremental_documents(collection, json_dir="./output/json"):
    """
    增量模式：只加载新文档（以 URL 过滤去重）

    参数:
        collection: ChromaDB collection 对象
        json_dir: JSON 文件目录

    返回: 需要新增的 Document 列表
    """
    # 1. 读取已索引的 URL 集合
    indexed_urls = set()
    if INDEXED_URLS_FILE.exists():
        try:
            with open(INDEXED_URLS_FILE, 'r', encoding='utf-8') as f:
                indexed_urls = set(json.load(f))
            print(f"已索引 URL 数量: {len(indexed_urls)}")
        except Exception as e:
            print(f"读取 URL 记录文件失败: {e}")
            indexed_urls = set()
    else:
        print("URL 记录文件不存在，将索引所有文件")

    # 2. 遍历 JSON 文件，检查是否已存在
    json_files = list(Path(json_dir).rglob("*.json"))
    new_documents = []
    skipped_count = 0

    for json_file in tqdm(json_files, desc="检查新文档"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            content = data.get("content", "")
            if len(content) < MIN_CONTENT_LENGTH:
                continue

            meta = data.get("metadata", {})
            source_url = meta.get("url", str(json_file))

            # 检查 URL 是否已存在
            if source_url in indexed_urls:
                skipped_count += 1
                continue

            # 生成唯一 ID（基于 URL 的 MD5）
            doc_id = hashlib.md5(source_url.encode('utf-8')).hexdigest()

            # 新文档，加入待处理列表
            doc = Document(
                text=content,
                metadata={
                    "title": meta.get("title", str(json_file.name)),
                    "url": source_url,
                    "source": str(json_file)
                },
                doc_id=doc_id
            )
            new_documents.append(doc)
            indexed_urls.add(source_url)  # 立即记录，避免重复

        except Exception as e:
            print(f"处理文件失败 {json_file}: {e}")

    # 3. 更新 URL 记录文件
    if new_documents:
        # 确保目录存在
        INDEXED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(INDEXED_URLS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(indexed_urls), f, ensure_ascii=False, indent=2)
        print(f"已更新 URL 记录，新增 {len(new_documents)} 条")

    print(f"\n跳过已存在: {skipped_count} 个")
    print(f"需要新增: {len(new_documents)} 个")

    return new_documents


def build_index(documents, incremental=False):
    """构建向量索引"""
    if not documents:
        print("没有文档可索引")
        return

    # 1. 创建 ChromaDB 客户端
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # 2. 处理集合
    if incremental:
        # 增量模式：使用现有集合或创建新集合
        try:
            collection = client.get_collection(COLLECTION_NAME)
            print(f"使用现有集合: {COLLECTION_NAME}")
        except Exception:
            collection = client.create_collection(COLLECTION_NAME)
            print(f"创建新集合: {COLLECTION_NAME}")
    else:
        # 非增量模式：删除旧集合并创建新集合
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"已删除旧集合: {COLLECTION_NAME}")
        except Exception:
            pass
        collection = client.create_collection(COLLECTION_NAME)
        print(f"创建新集合: {COLLECTION_NAME}")

    vector_store = ChromaVectorStore(chroma_collection=collection)

    # 3. 显式创建存储上下文
    from llama_index.core.storage.storage_context import StorageContext
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("开始构建索引...")
    print(f"文档数量: {len(documents)}")
    print(f"存储目录: {CHROMA_DB_DIR}")

    # 4. 构建索引时传入 storage_context
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    # 5. 验证写入结果
    doc_count = collection.count()
    print(f"\n写入后集合中文档数量: {doc_count}")
    print(f"向量库已保存到: {CHROMA_DB_DIR}")
    print(f"集合名称: {COLLECTION_NAME}")

    if doc_count == 0:
        print("⚠️ 警告：向量库中没有任何文档，请检查数据或嵌入模型配置。")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="构建向量索引")
    parser.add_argument("--incremental", action="store_true", help="增量索引模式")
    args = parser.parse_args()
    
    print("=== RAG 向量索引构建 ===")
    print(f"JSON 目录: {JSON_DIR}")
    print(f"ChromaDB 目录: {CHROMA_DB_DIR}")
    print(f"增量模式: {args.incremental}")
    print()

    if args.incremental:
        # 增量模式：使用带去重的加载函数
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_or_create_collection(COLLECTION_NAME)
        documents = load_incremental_documents(collection, json_dir=str(JSON_DIR))

        if not documents:
            print("没有新文档需要索引")
            sys.exit(0)
    else:
        # 全量模式：使用原来的全量加载
        documents = load_documents()
        # 全量构建时保存 URL 记录
        save_indexed_urls(documents)

    build_index(documents, incremental=args.incremental)