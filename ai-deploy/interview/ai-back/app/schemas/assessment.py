from pydantic import BaseModel, Field
from typing import List


class AssessmentInsight(BaseModel):
    ai_insight: str = Field(description="150-200字的纯文本综合鉴定段落，绝对不能包含任何 Markdown 符号")
    top_strengths: List[str] = Field(
        description="候选人在多次面试中展现出的最稳定的2-3个核心技术优势，每条控制在15字以内"
    )
    priority_actions: List[str] = Field(
        description="优先级从高到低排列的2-3条行动建议，每条必须是立刻可执行的具体技术学习指令（如：系统突击 Vue3 响应式原理，侧重手写代码实战），每条控制在25字以内"
    )
