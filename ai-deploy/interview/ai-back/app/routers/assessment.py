import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.dependencies import get_db, get_current_user_id
from app.models.report import Report
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentInsight
from app.prompts.assessment import get_dashboard_insight_prompt
from app.services.llm import llm

router = APIRouter()


@router.get("/api/assessment/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 极速查询，验证缓存是否有效
    current_report_count = db.query(Report).filter(Report.owner_id == user_id).count()
    assessment_cache = db.query(Assessment).filter(Assessment.owner_id == user_id).first()

    if (assessment_cache and 
        assessment_cache.total_interviews == current_report_count and 
        assessment_cache.top_strengths and 
        assessment_cache.top_strengths != "[]"):
        print("命中完整综合评估缓存，直接返回！")
        cached = {
            "total_interviews": assessment_cache.total_interviews,
            "avg_score": assessment_cache.avg_score,
            "total_duration": assessment_cache.total_duration,
            "radar_data": json.loads(assessment_cache.radar_data),
            "trend_data": json.loads(assessment_cache.trend_data),
            "ai_insight": assessment_cache.ai_insight,
        }
        # 延伸字段（兼容旧缓存没有的情况）
        try:
            cached["top_strengths"] = json.loads(assessment_cache.top_strengths) if assessment_cache.top_strengths else []
            cached["priority_actions"] = json.loads(assessment_cache.priority_actions) if assessment_cache.priority_actions else []
            cached["global_blank_tags"] = json.loads(assessment_cache.global_blank_tags) if assessment_cache.global_blank_tags else []
        except Exception:
            cached["top_strengths"] = []
            cached["priority_actions"] = []
            cached["global_blank_tags"] = []
        return cached

    print("面试次数有更新 (或无缓存)，开始重新聚合数据并呼叫大模型...")
    reports = db.query(Report).filter(Report.owner_id == user_id).order_by(Report.id.asc()).all()

    if not reports:
        empty_radar = {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0}
        empty_insight = "您还没有进行过面试，赶快去大厅选择一个心仪的岗位，开启您的第一次沉浸式模拟面试吧！"

        if not assessment_cache:
            new_cache = Assessment(
                owner_id=user_id, total_interviews=0, avg_score=0, total_duration=0,
                radar_data=json.dumps(empty_radar), trend_data="[]", ai_insight=empty_insight
            )
            db.add(new_cache)
            db.commit()

        return {
            "total_interviews": 0, "avg_score": 0, "total_duration": 0,
            "radar_data": empty_radar, "trend_data": [], "ai_insight": empty_insight,
            "top_strengths": [], "priority_actions": [], "global_blank_tags": []
        }

    # ============================================================
    # 数据聚合：雷达均值、趋势、全局盲区词频统计
    # ============================================================
    total_score = 0
    total_duration = sum(r.duration for r in reports if r.duration is not None)
    valid_radar_count = 0
    radar_sum = {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0}
    trend_data = []
    recent_evaluations = []

    all_blank_tags = []      # 聚合所有报告的盲区标签
    all_mastered_tags = []   # 聚合所有报告的掌握技能标签

    for r in reports:
        try:
            content = json.loads(r.content)
            score = content.get("score", 0)
            total_score += score
            time_str = r.created_at.strftime("%m-%d") if getattr(r, 'created_at', None) else "未知"
            trend_data.append({"date": time_str, "score": score, "job": r.target_job})

            radar = content.get("radar_data")
            if radar:
                valid_radar_count += 1
                for key in radar_sum:
                    radar_sum[key] += radar.get(key, 0)

            eval_text = content.get("evaluation")
            if eval_text:
                recent_evaluations.append(f"岗位【{r.target_job}】: {eval_text}")

            # 新增：聚合结构化标签
            for tag in content.get("knowledge_blank_tags", []):
                all_blank_tags.append(tag)
            for tag in content.get("skill_breakdown", []):
                if isinstance(tag, dict) and tag.get("status") == "掌握":
                    all_mastered_tags.append(tag.get("skill", ""))

        except Exception:
            continue

    avg_score = round(total_score / len(reports))
    avg_radar = {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0}
    if valid_radar_count > 0:
        for key in radar_sum:
            avg_radar[key] = round(radar_sum[key] / valid_radar_count)

    # 全局高频盲区 Top5（词频统计）
    blank_counter = Counter(all_blank_tags)
    global_blank_tags = [{"tag": tag, "count": cnt} for tag, cnt in blank_counter.most_common(5)]

    # 掌握技能 Top5
    mastered_counter = Counter(all_mastered_tags)
    top_mastered_tags = [tag for tag, _ in mastered_counter.most_common(5)]

    # ============================================================
    # 呼叫大模型生成 AI 洞察（注入结构化证据）
    # ============================================================
    ai_insight = "您的各项能力正在稳步提升，请继续保持练习！"
    top_strengths = []
    priority_actions = []
    recent_3_evals = recent_evaluations[-3:]

    if recent_3_evals:
        blank_tags_str = "、".join([item["tag"] for item in global_blank_tags]) if global_blank_tags else "暂无"
        mastered_str = "、".join(top_mastered_tags) if top_mastered_tags else "暂无"

        system_prompt = get_dashboard_insight_prompt()
        parser = JsonOutputParser(pydantic_object=AssessmentInsight)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}\n\n【输出格式要求】\n{format_instructions}"),
            ("user",
             "【已掌握技能清单（高频出现）】：{mastered_tags}\n\n"
             "【高频盲区标签（高频出现的弱点）】：{blank_tags}\n\n"
             "【近期面试综合评语记录】：\n{evals_text}\n\n"
             "请基于以上证据，严格按格式生成综合鉴定。")
        ])

        chain = prompt | llm | parser

        try:
            insight_data = await chain.ainvoke({
                "system_prompt": system_prompt,
                "mastered_tags": mastered_str,
                "blank_tags": blank_tags_str,
                "evals_text": "\n".join(recent_3_evals),
                "format_instructions": parser.get_format_instructions()
            })
            ai_insight = insight_data.get("ai_insight", ai_insight)
            top_strengths = insight_data.get("top_strengths", [])
            priority_actions = insight_data.get("priority_actions", [])
        except Exception as e:
            print(f"⚠️ 综合评价生成失败，降级使用默认文本: {e}")

    # ============================================================
    # 更新缓存（兼容新增字段）
    # ============================================================
    radar_json_str = json.dumps(avg_radar)
    trend_json_str = json.dumps(trend_data)
    duration_minutes = total_duration // 60

    cache_fields = dict(
        total_interviews=len(reports),
        avg_score=avg_score,
        total_duration=duration_minutes,
        radar_data=radar_json_str,
        trend_data=trend_json_str,
        ai_insight=ai_insight,
    )
    # 新字段写入（setattr 逐一赋值兼容旧 ORM 列不存在的情况）
    extra_fields = dict(
        top_strengths=json.dumps(top_strengths, ensure_ascii=False),
        priority_actions=json.dumps(priority_actions, ensure_ascii=False),
        global_blank_tags=json.dumps(global_blank_tags, ensure_ascii=False),
    )

    if assessment_cache:
        for k, v in {**cache_fields, **extra_fields}.items():
            try:
                setattr(assessment_cache, k, v)
            except Exception:
                pass
    else:
        new_assessment = Assessment(owner_id=user_id, **cache_fields)
        for k, v in extra_fields.items():
            try:
                setattr(new_assessment, k, v)
            except Exception:
                pass
        db.add(new_assessment)

    db.commit()

    return {
        "total_interviews": len(reports),
        "avg_score": avg_score,
        "total_duration": duration_minutes,
        "radar_data": avg_radar,
        "trend_data": trend_data,
        "ai_insight": ai_insight,
        "top_strengths": top_strengths,
        "priority_actions": priority_actions,
        "global_blank_tags": global_blank_tags,
    }
