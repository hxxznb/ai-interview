from pydantic import BaseModel, Field
from typing import List, Optional

class EvaluationResult(BaseModel):
    comprehension_score: int = Field(description="回答质量打分 (1-10)")
    mastered_skills: List[str] = Field(default_factory=list, description="提取出的已掌握或准确回答的技能点名词")
    knowledge_blank: List[str] = Field(default_factory=list, description="候选人表示不会或回答完全错误的技能/盲区名词")
    topic_exhausted: bool = Field(description="当前话题是否已经聊够了，或者候选人表示不会导致无法继续深入")
    suggested_next_action: str = Field(description="建议的主动作: SEARCH_DEEPER (深挖当前话题), SWITCH_TOPIC (换新话题)")
    search_query: str = Field(default="", description="如果建议 SEARCH_DEEPER 或 SWITCH_TOPIC，提供用于 RAG 检索的具体知识点名词或短语，如果是敷衍则留空")
