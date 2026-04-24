import streamlit as st
import requests

# 页面配置
st.set_page_config(
    page_title=" 知识库",
    page_icon="📚",
    layout="centered"
)

st.title("📚  知识库 RAG 助手")
st.caption("基于本地向量检索 + 通义千问大模型")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    api_url = st.text_input(
        "API 地址",
        value="http://localhost:8000/query",
        help="填写你的 FastAPI 服务地址"
    )
    top_k = st.slider("检索片段数", min_value=1, max_value=10, value=3)

    st.divider()
    st.caption("知识库包含 Java 面试、数据库、分布式、AI 应用开发等内容。")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📎 参考来源"):
                for src in msg["sources"]:
                    st.markdown(f"- [{src['title']}]({src['url']}) (相似度: {src['score']:.3f})")

# 用户输入
if prompt := st.chat_input("请输入你的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用 API
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response = requests.post(
                    api_url,
                    json={"question": prompt, "top_k": top_k},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "抱歉，未获取到回答。")
                    sources = data.get("sources", [])

                    st.markdown(answer)

                    if sources:
                        with st.expander("📎 参考来源"):
                            for src in sources:
                                st.markdown(
                                    f"- [{src['title']}]({src['url']}) "
                                    f"(相似度: {src['score']:.3f})"
                                )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    st.error(f"API 请求失败: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到 API 服务，请确认服务已启动。")
            except Exception as e:
                st.error(f"发生错误: {e}")