#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api.py - FastAPI 服务入口
提供 RAG 知识库查询接口
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.dashscope import DashScope
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from config import DASHSCOPE_API_KEY, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_PATH, HOST, PORT, DEBUG

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- 全局配置（启动时加载一次） ----------
# 1. 本地嵌入模型
Settings.embed_model = HuggingFaceEmbedding(
    model_name=str(EMBEDDING_MODEL_PATH),
    device="cpu"
)

# 2. LLM 配置（与 query_cli.py 完全一致）
model_name = os.getenv("DASHSCOPE_MODEL", "qwen-max")
Settings.llm = DashScope(
    model_name=model_name,
    api_key=DASHSCOPE_API_KEY
)

# 3. 自定义 Prompt 模板
CUSTOM_PROMPT = PromptTemplate(
    "你是一个专业的Java技术知识库助手。请根据以下参考资料，用中文清晰、准确地回答用户的问题。\n"
    "参考资料：\n{context_str}\n"
    "问题：{query_str}\n"
    "回答："
)

# 4. 加载向量索引
try:
    db = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = db.get_collection(CHROMA_COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    logger.info(f"向量索引加载成功，文档数：{collection.count()}")
except Exception as e:
    logger.error(f"向量索引加载失败：{e}")
    raise

# 5. 默认查询引擎（top_k=3）
query_engine = index.as_query_engine(
    similarity_top_k=3,
    text_qa_template=CUSTOM_PROMPT
)

# ---------- FastAPI 应用实例 ----------
app = FastAPI(
    title="JavaGuide RAG 知识库 API",
    description="基于本地向量检索 + DashScope 大模型的知识问答服务",
    version="2.0.0"
)

# 跨域配置（允许所有来源，生产环境建议限制具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 请求/响应模型 ----------
class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1)
    top_k: Optional[int] = Field(3, description="返回的参考片段数量", ge=1, le=10)

class SourceItem(BaseModel):
    title: str
    url: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]

class HealthResponse(BaseModel):
    status: str
    index_document_count: int
    llm_model: str

# ---------- 路由定义 ----------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "index_document_count": collection.count(),
        "llm_model": model_name
    }

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(req: QueryRequest):
    """
    知识库查询接口
    - question: 自然语言问题
    - top_k: 返回参考片段数量（默认3）
    """
    try:
        logger.info(f"收到问题：{req.question[:50]}...")

        # 如果请求的 top_k 与默认不同，临时创建新引擎
        if req.top_k != 3:
            temp_engine = index.as_query_engine(
                similarity_top_k=req.top_k,
                text_qa_template=CUSTOM_PROMPT
            )
            response = temp_engine.query(req.question)
        else:
            response = query_engine.query(req.question)

        # 提取来源信息
        sources = []
        for node in response.source_nodes:
            sources.append(SourceItem(
                title=node.metadata.get("title", "未知"),
                url=node.metadata.get("url", ""),
                score=round(node.score, 4) if node.score else 0.0
            ))

        logger.info(f"生成回答成功，来源数：{len(sources)}")
        return QueryResponse(
            answer=str(response),
            sources=sources
        )

    except Exception as e:
        logger.error(f"查询失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="知识库查询失败，请稍后重试")


# ---------- 启动入口（用于直接运行调试） ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "rag.api:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
