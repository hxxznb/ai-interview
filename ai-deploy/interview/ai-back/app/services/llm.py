import os
import dashscope
from langchain_community.chat_models.tongyi import ChatTongyi

from app.config import settings

# 统一设置 API Key
dashscope.api_key = settings.DASHSCOPE_API_KEY
os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY

# 全局唯一 LLM 实例
llm = ChatTongyi(model=settings.LLM_MODEL)
