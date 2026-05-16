from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.schemas.recent_diagnosis import IntentResult


def analyze_user_intent(llm, job_title: str, last_question: str, user_answer: str) -> dict:
    """
    智能体大脑前置皮层：分析候选人意图，决定 RAG 检索策略
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个 AI 面试系统的"前置意图路由大脑"。
你的唯一任务是分析面试官的上一个问题和候选人的最新回答，判断接下来是否需要去题库中搜索专业知识。

【决策路由表】
1. 正常回答/深度探讨 -> action: "SEARCH" 
   - search_query 提炼出核心技术词（如 "Vue 响应式 原理"）。
2. 表示不知道/敷衍/无意义输入（如"不知道"、"没用过"、"?"、"当然"） -> action: "SKIP" 
   - search_query 为 ""。
3. 主动转移话题（如"我没用过Vue，但我用过React"） -> action: "REWRITE"
   - search_query 提取新话题（如 "React 核心原理"）。

【强制输出格式】
必须输出纯净的 JSON 字符串，严格符合以下结构，不要有任何多余的 Markdown 标记：
{{
    "action": "SEARCH",
    "search_query": "搜索词"
}}"""),
        ("user", "面试岗位：{job_title}\n上一个问题：{last_question}\n候选人回答：{user_answer}")
    ])

    # 组装链并要求输出 JSON
    parser = JsonOutputParser(pydantic_object=IntentResult)
    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "job_title": job_title,
            "last_question": last_question,
            "user_answer": user_answer
        })
        return result
    except Exception as e:
        # 兜底机制：如果大模型偶尔抽风没返回 JSON，强行进入通用搜索
        print(f"⚠️ [路由降级] 意图分析解析失败: {e}")
        return {"action": "SEARCH", "search_query": f"{last_question} {user_answer}"}
