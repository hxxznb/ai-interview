import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.dependencies import get_db, get_current_user_id
from app.models.report import Report
from app.models.recent_diagnosis import RecentDiagnosis
from app.schemas.recent_diagnosis import FirstAidPrescription
from app.prompts.recent_diagnosis import get_recent_diagnosis_prompt
from app.services.llm import llm

router = APIRouter()


@router.get("/api/assessment/recent")
async def get_recent_diagnosis_data(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 极速查询，验证缓存是否有效
    current_report_count = db.query(Report).filter(Report.owner_id == user_id).count()
    diagnosis_cache = db.query(RecentDiagnosis).filter(RecentDiagnosis.owner_id == user_id).first()

    if (diagnosis_cache and 
        diagnosis_cache.total_interviews == current_report_count and 
        diagnosis_cache.blank_frequency and 
        diagnosis_cache.blank_frequency != "[]"):
        print("⚡ 命中完整近期诊断缓存，直接返回！")
        result = {
            "has_data": current_report_count > 0,
            "multi_line_data": json.loads(diagnosis_cache.multi_line_data),
            "delta_data": json.loads(diagnosis_cache.delta_data),
            "weakness_tags": json.loads(diagnosis_cache.weakness_tags),
            "expert_advice": diagnosis_cache.expert_advice,
        }
        try:
            result["blank_frequency"] = json.loads(diagnosis_cache.blank_frequency) if diagnosis_cache.blank_frequency else []
        except Exception:
            result["blank_frequency"] = []
        return result

    print("⏳ 面试次数有更新 (或无缓存)，开始重新生成近期诊断...")
    recent_reports = db.query(Report).filter(Report.owner_id == user_id).order_by(Report.id.desc()).limit(5).all()

    if not recent_reports:
        if not diagnosis_cache:
            new_cache = RecentDiagnosis(
                owner_id=user_id, total_interviews=0,
                multi_line_data="[]", delta_data="{}", weakness_tags="[]",
                expert_advice="暂无数据，快去大厅开启第一次模拟面试吧！"
            )
            db.add(new_cache)
            db.commit()
        return {"has_data": False, "message": "暂无近期面试数据"}

    recent_reports.reverse()
    multi_line_data = []
    recent_evaluations = []
    all_blank_tags = []          # 近5场所有的盲区标签列表

    for r in recent_reports:
        try:
            content = json.loads(r.content)
            time_str = r.created_at.strftime("%m-%d") if getattr(r, 'created_at', None) else "未知"
            radar = content.get("radar_data",
                                {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0})

            multi_line_data.append({
                "date": time_str,
                "tech": radar.get("tech", 0), "logic": radar.get("logic", 0),
                "communication": radar.get("communication", 0), "experience": radar.get("experience", 0),
                "potential": radar.get("potential", 0)
            })

            eval_text = content.get("evaluation")
            if eval_text:
                recent_evaluations.append(f"【{r.target_job}】: {eval_text}")

            # 直接从结构化标签采集（优于纯文本分析）
            for tag in content.get("knowledge_blank_tags", []):
                if tag:
                    all_blank_tags.append(tag)

        except Exception:
            continue

    # delta_data（相比上一场的升降）
    delta_data = {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0}
    if len(multi_line_data) >= 2:
        latest = multi_line_data[-1]
        previous = multi_line_data[-2]
        for key in delta_data.keys():
            delta_data[key] = latest[key] - previous[key]

    # 近5场盲区词频排行
    blank_counter = Counter(all_blank_tags)
    blank_frequency = [{"tag": tag, "count": cnt} for tag, cnt in blank_counter.most_common(8)]

    # ============================================================
    # 呼叫大模型生成急救处方（注入结构化盲区证据）
    # ============================================================
    tags = []
    advice = "您的数据正在稳定积累，请继续保持练习节奏。"

    blank_tags_str = "、".join([item["tag"] for item in blank_frequency]) if blank_frequency else "（暂无）"

    if recent_evaluations:
        system_prompt = get_recent_diagnosis_prompt()
        parser = JsonOutputParser(pydantic_object=FirstAidPrescription)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}\n\n【输出格式要求】\n{format_instructions}"),
            ("user",
             "【近5场直接采集到的技能盲区标签（高优先参考）】：{blank_tags}\n\n"
             "【近5次面试评价记录】：\n{evals_text}\n\n"
             "请严格开具急救处方，weakness_tags 必须直接使用上方盲区标签中的具体名词。")
        ])

        chain = prompt | llm | parser

        try:
            prescription_data = await chain.ainvoke({
                "system_prompt": system_prompt,
                "blank_tags": blank_tags_str,
                "evals_text": "\n".join(recent_evaluations),
                "format_instructions": parser.get_format_instructions()
            })

            tags = prescription_data.get("weakness_tags", [])
            advice = prescription_data.get("expert_advice", advice)

        except Exception as e:
            # 大模型失败时用词频结果做降级 fallback
            tags = [item["tag"] for item in blank_frequency[:3]]
            print(f"⚠️ 近期诊断 AI 生成失败，降级使用词频标签: {e}")

    # ============================================================
    # 更新缓存表
    # ============================================================
    multi_line_json = json.dumps(multi_line_data)
    delta_json = json.dumps(delta_data)
    tags_json = json.dumps(tags)
    blank_frequency_json = json.dumps(blank_frequency, ensure_ascii=False)

    if diagnosis_cache:
        diagnosis_cache.total_interviews = current_report_count
        diagnosis_cache.multi_line_data = multi_line_json
        diagnosis_cache.delta_data = delta_json
        diagnosis_cache.weakness_tags = tags_json
        diagnosis_cache.expert_advice = advice
        try:
            diagnosis_cache.blank_frequency = blank_frequency_json
        except Exception:
            pass
    else:
        new_cache = RecentDiagnosis(
            owner_id=user_id, total_interviews=current_report_count,
            multi_line_data=multi_line_json, delta_data=delta_json,
            weakness_tags=tags_json, expert_advice=advice
        )
        try:
            new_cache.blank_frequency = blank_frequency_json
        except Exception:
            pass
        db.add(new_cache)

    db.commit()

    return {
        "has_data": True,
        "multi_line_data": multi_line_data,
        "delta_data": delta_data,
        "weakness_tags": tags,
        "expert_advice": advice,
        "blank_frequency": blank_frequency,
    }
