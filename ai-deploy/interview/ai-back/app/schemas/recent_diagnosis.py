from pydantic import BaseModel, Field
from typing import List


class FirstAidPrescription(BaseModel):
    weakness_tags: List[str] = Field(
        description="高频踩坑点。提取1到3个具体的名词或缺陷短语（如：Vue3响应式、沟通语速过快），必须是一个列表数组"
    )
    expert_advice: str = Field(
        description="急救动作。只用一句话（60字以内），给出立刻能执行的具体突击指令"
    )


class IntentResult(BaseModel):
    action: str = Field(description="必须是 SEARCH, SKIP, 或 REWRITE 中的一个")
    search_query: str = Field(description="用于去数据库检索的具体知识点，如果 action 是 SKIP 则为空字符串")
