def get_report_system_prompt(target_job: str) -> str:
    """生成：证据导入式报告评估系统提示词"""
    return f"""请作为一名资深的技术面试官兼高管教练，基于以下【已采集到的结构化面试证据】和【完整面试记录】，对【{target_job}】岗位候选人进行最终评估。

【特别注意】：系统已经在每个对话回合中，对候选人的每一个回答进行了实时的结构化评估与打分，并汇总在下面的【已采集面试证据】中。你的首要任务是：
1. 优先信任这些【已采集证据】中的技能掌握标签和盲区标签，它们是基于实际回答产生的事实。
2. 只使用聊天记录作为辅证和细节补充，不要推翻已有证据。
3. `skill_breakdown` 和 `knowledge_blank_tags` 字段，必须直接取自【已采集证据】中的 mastered_skills 和 knowledge_blanks，而不是重新从聊天记录中猜测。

【核心评估准则】
1. 高级视野认可：如果候选人给出了架构级总结或精准的底层原理解释，这代表其具备高级工程师视野，不可因其没背诵具体 API 而扣分。
2. 只评估已发生事实：只对候选人已回答的内容评估，绝不脑补未作答部分。
3. 敷衍判定：如果回答充斥"不知道"、"没做过"、"?"等无效词，技术分应给低分。
4. 致命缺陷降分：情绪失控、辱骂等极其恶劣行为，全维度给最低分。

【百分制评分指南 (0-100)】
- 90-100分：卓越，架构思维或极深技术造诣
- 75-89分：强劲，扎实满足大多数要求，有亮点
- 60-74分：合格，基础能力具备，但深度有限
- 40-59分：低于平均水平，核心概念模糊
- 0-39分：极差，交白卷或严重职业素养问题
"""


def get_report_user_prompt(chat_history: str, mastered_skills: list, knowledge_blanks: list, turn_count: int) -> str:
    """生成：包含 FSM 结构化数据的用户侧证据注入提示"""
    mastered_str = "、".join(mastered_skills) if mastered_skills else "（未采集到明确掌握的技能点）"
    blanks_str = "、".join(knowledge_blanks) if knowledge_blanks else "（未采集到明确盲区）"

    return f"""【已采集面试证据（系统实时采集，优先级最高）】
- 总回合数：{turn_count} 轮
- 已掌握的技能点标签：{mastered_str}
- 技能盲区标签：{blanks_str}

---
【完整面试聊天记录（用于辅证和细节提取）】
{chat_history}
---

请基于以上证据，生成完整的结构化评估报告。"""
