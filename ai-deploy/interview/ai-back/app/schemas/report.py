from pydantic import BaseModel, Field
from typing import List, Optional


class RadarData(BaseModel):
    tech: int = Field(description="技术深度评分 (0-100)")
    logic: int = Field(description="逻辑思维评分 (0-100)")
    communication: int = Field(description="沟通表达评分 (0-100，如出现辱骂则给0分)")
    experience: int = Field(description="项目经验评分 (0-100)")
    potential: int = Field(description="发展潜力评分 (0-100)")


class SkillStatus(BaseModel):
    skill: str = Field(description="技能点名称，例如 Vue3响应式、TCP三次握手")
    status: str = Field(description="掌握程度: '掌握' / '盲区' / '部分了解'")
    comment: str = Field(description="一句话点评，例如：能说出核心原理，但缺乏实战细节")


class AssessmentReport(BaseModel):
    score: int = Field(description="综合得分 (0-100)")
    evaluation: str = Field(description="对候选人整体表现的综合总结，100字左右")
    tech_ability: str = Field(description="详细的技术能力评价，指出其技术深度的亮点与不足")
    communication: str = Field(description="沟通表达与逻辑思维评价")
    strengths: List[str] = Field(description="核心优势列表，最多3条")
    weaknesses: List[str] = Field(description="需要提升的不足之处，最多3条")
    radar_data: RadarData = Field(description="多维度雷达图评分")
    skill_breakdown: List[SkillStatus] = Field(
        default_factory=list,
        description="逐技能点画像列表，直接基于面试中采集到的掌握/盲区标签生成"
    )
    knowledge_blank_tags: List[str] = Field(
        default_factory=list,
        description="候选人的核心盲区标签列表，直接来自 Evaluator 采集的 knowledge_blank 字段"
    )
    improvement_advice: str = Field(
        description="一段针对候选人的个性化提升建议，基于盲区标签，给出最优先应该补强的方向（80字以内）"
    )
