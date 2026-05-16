import os

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.services.llm import llm

# 唤醒向量数据库组件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
embeddings = DashScopeEmbeddings(model=settings.EMBEDDING_MODEL)
vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)


def get_rag_response(user_message: str, chat_history_str: str, system_prompt: str, search_query: str,
                     category_filter: str = "front", doc_type: str = None) -> str:
    """
    RAG 对话核心引擎
    """
    # 1. 检索 RAG 资料 (只有非开场阶段，才去查题库)
    docs = []
    if search_query != "SKIP_SEARCH":
        try:
            custom_filter = {"category": {"$in": [category_filter, "general"]}}
            if doc_type:
                custom_filter = {
                    "$and": [
                        {"category": {"$in": [category_filter, "general"]}},
                        {"type": doc_type}
                    ]
                }
                
            retriever = vectordb.as_retriever(
                search_kwargs={
                    "k": 3,
                    "filter": custom_filter
                }
            )
            docs = retriever.invoke(search_query)
        except Exception as e:
            print(f"⚠️ 检索失败或未找到该分类资料: {e}")

    # 将搜到的知识拼成文本
    context_text = "\n\n".join([doc.page_content for doc in docs]) if docs else "未搜索到特定题库资料，请正常应对。"
    print("\n====== [DEBUG] 喂给大模型的 RAG 资料 ======")
    print(context_text)
    print("=========================================\n")

    # 2. 组装终极 Prompt
    safe_system_template = system_prompt + "\n\n【当前面试考核知识点与标准答案】\n{context}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", safe_system_template),
        ("user", "【历史聊天记录】\n{chat_history}\n\n【候选人最新回复】\n{user_input}")
    ])

    chain = prompt | llm | StrOutputParser()

    # 3. 执行推理
    response = chain.invoke({
        "context": context_text,
        "chat_history": chat_history_str,
        "user_input": user_message
    })

    return response
