from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.schemas.evaluator import EvaluationResult

def evaluate_user_response(llm, job_title: str, last_question: str, user_answer: str) -> dict:
    """
    智能体大脑前置皮层：分析候选人回答质量、盲区，决定下一阶段的状态路由。
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个 AI 面试系统的"前置结构化评估大脑"。
你的任务是极其客观地分析面试官的上一个问题和候选人的最新回答。

【输出要求】
必须输出纯净的 JSON 字符串，严格符合以下字段：
1. comprehension_score (1-10) 整数
2. mastered_skills (List[str]): 答对的技能专有名词（如 "Vue3响应式"）
3. knowledge_blank (List[str]): 候选人明确说不会、不知道、或者回答牛头不对马嘴的技能点
4. topic_exhausted (bool): 如果候选人说不会，或回答极其敷衍，或者该话题已经没必要再深挖，则为 true
5. suggested_next_action: "SEARCH_DEEPER" 还是 "SWITCH_TOPIC"
6. search_query: 如果 action 是深挖或换新话题，提炼个精简的检索词。如果是彻底敷衍，留空。

注意：绝对不要有 Markdown 格式（如 ```json 等），只输出大括号开始的 JSON 结构体！"""),
        ("user", "面试岗位：{job_title}\n上一个问题：{last_question}\n候选人回答：{user_answer}")
    ])

    parser = JsonOutputParser(pydantic_object=EvaluationResult)
    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "job_title": job_title,
            "last_question": last_question,
            "user_answer": user_answer
        })
        return result
    except Exception as e:
        print(f"⚠️ [路由降级] 结构化评估解析失败: {e}")
        return {
            "comprehension_score": 5,
            "mastered_skills": [],
            "knowledge_blank": [],
            "topic_exhausted": False,
            "suggested_next_action": "SEARCH_DEEPER",
            "search_query": f"{last_question} {user_answer}"
        }
