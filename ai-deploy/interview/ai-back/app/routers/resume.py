"""
简历分析路由
提供完整的简历上传、异步分析、审阅、构建和历史查询接口
"""
import json
import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_db, get_current_user_id
from app.models.resume import ResumeAnalysis, ResumeBlock
from app.services.resume_engine import (
    parse_docx_to_blocks,
    analyze_single_block,
    generate_overall_evaluation,
    build_output_docx,
    UPLOAD_DIR,
)
from app.services.llm import llm

router = APIRouter(prefix="/api/resume", tags=["resume"])


# ============================================================
# 后台异步分析任务
# ============================================================
def run_analysis_task(analysis_id: int, file_path: str, job_target: str):
    """
    在后台线程中逐块分析简历，完成后更新数据库状态。
    采用独立 DB session，避免与请求 session 冲突。
    """
    db: Session = SessionLocal()
    try:
        analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
        if not analysis:
            return

        analysis.status = "analyzing"
        db.commit()

        # 1. 解析 Word 文档为块
        raw_blocks = parse_docx_to_blocks(file_path)

        # 2. 写入初始块记录（全部 pending）
        for b in raw_blocks:
            block = ResumeBlock(
                analysis_id=analysis_id,
                block_index=b["block_index"],
                section_title=b["section_title"],
                original_text=b["original_text"],
                block_status="pending",
            )
            db.add(block)
        db.commit()

        # 3. 刷新获取真实 ID，逐块调用 LLM 分析
        blocks_in_db = (
            db.query(ResumeBlock)
            .filter(ResumeBlock.analysis_id == analysis_id)
            .order_by(ResumeBlock.block_index)
            .all()
        )

        for block in blocks_in_db:
            result = analyze_single_block(
                block_text=block.original_text,
                section_title=block.section_title,
                job_target=job_target,
                llm=llm,
            )
            block.suggested_text = result["suggested_text"]
            block.suggestion_reason = result["suggestion_reason"]
            block.block_status = "done"
            db.commit()

        # 4. 整体评价
        all_block_dicts = [
            {"section_title": b.section_title, "original_text": b.original_text}
            for b in blocks_in_db
        ]
        overall = generate_overall_evaluation(all_block_dicts, job_target, llm)
        analysis.overall_strengths = overall["overall_strengths"]
        analysis.overall_weaknesses = overall["overall_weaknesses"]
        analysis.job_match_score = overall["job_match_score"]
        analysis.status = "reviewed"
        db.commit()

    except Exception as e:
        print(f"[ResumeRouter] 后台分析任务异常: {e}")
        db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).update({"status": "failed"})
        db.commit()
    finally:
        db.close()


# ============================================================
# 接口 1：上传简历，启动分析
# ============================================================
@router.post("/analyze")
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_target: str = Form(default="通用岗位"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 格式的 Word 文件")

    # 保存到本地磁盘
    safe_name = f"upload_{user_id}_{int(__import__('time').time())}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 创建分析记录
    analysis = ResumeAnalysis(
        owner_id=user_id,
        job_target=job_target,
        original_file_path=str(file_path),
        original_filename=file.filename,
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 启动后台任务（不阻塞当前请求）
    background_tasks.add_task(run_analysis_task, analysis.id, str(file_path), job_target)

    return {"analysis_id": analysis.id, "status": "pending", "msg": "分析任务已启动"}


# ============================================================
# 接口 2：轮询分析进度
# ============================================================
@router.get("/analyze/{analysis_id}/progress")
def get_analysis_progress(
    analysis_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    blocks = (
        db.query(ResumeBlock)
        .filter(ResumeBlock.analysis_id == analysis_id)
        .order_by(ResumeBlock.block_index)
        .all()
    )

    blocks_data = [
        {
            "id": b.id,
            "block_index": b.block_index,
            "section_title": b.section_title,
            "original_text": b.original_text,
            "suggested_text": b.suggested_text,
            "suggestion_reason": b.suggestion_reason,
            "is_accepted": b.is_accepted,
            "block_status": b.block_status,
        }
        for b in blocks
    ]

    # 解析整体评价 JSON
    strengths, weaknesses = [], []
    try:
        if analysis.overall_strengths:
            strengths = json.loads(analysis.overall_strengths)
        if analysis.overall_weaknesses:
            weaknesses = json.loads(analysis.overall_weaknesses)
    except Exception:
        pass

    return {
        "analysis_id": analysis_id,
        "status": analysis.status,
        "job_target": analysis.job_target,
        "original_filename": analysis.original_filename,
        "blocks": blocks_data,
        "overall": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "job_match_score": analysis.job_match_score,
        },
    }


# ============================================================
# 接口 3：用户接受 / 忽略某块建议
# ============================================================
class AcceptBlockRequest(BaseModel):
    is_accepted: bool


@router.patch("/block/{block_id}/accept")
def update_block_decision(
    block_id: int,
    body: AcceptBlockRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    block = db.query(ResumeBlock).filter(ResumeBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="块不存在")

    # 确认属于本人
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == block.analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=403, detail="无权操作")

    block.is_accepted = body.is_accepted
    db.commit()
    return {"ok": True}


# ============================================================
# 接口 4：开始构建，生成最终 Word 文件
# ============================================================
@router.post("/analyze/{analysis_id}/build")
def build_resume(
    analysis_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    analysis.status = "building"
    db.commit()

    blocks = (
        db.query(ResumeBlock)
        .filter(ResumeBlock.analysis_id == analysis_id)
        .order_by(ResumeBlock.block_index)
        .all()
    )

    blocks_data = [
        {
            "block_index": b.block_index,
            "section_title": b.section_title,
            "original_text": b.original_text,
            "suggested_text": b.suggested_text,
            "is_accepted": b.is_accepted,
        }
        for b in blocks
    ]

    output_paths = build_output_docx(analysis_id, analysis.original_file_path, blocks_data)
    analysis.output_file_path = output_paths["full"]
    analysis.status = "done"
    db.commit()

    return {"ok": True, "analysis_id": analysis_id, "msg": "简历构建完成"}


# ============================================================
# 接口 5：下载最终 Word 文件
# ============================================================
@router.get("/analyze/{analysis_id}/download")
def download_resume(
    analysis_id: int,
    mode: str = Query("full", description="下载模式: full 或 content"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis or not analysis.output_file_path:
        raise HTTPException(status_code=404, detail="文件尚未生成")

    output_path = Path(analysis.output_file_path)
    if mode == "content":
        output_path = Path(str(output_path).replace("_full.docx", "_content.docx"))

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="文件已被清除，请重新构建")

    filename_suffix = "排版修改版" if mode == "content" else "原格式保留版"
    return FileResponse(
        path=str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"AI{filename_suffix}_{analysis.original_filename}",
    )


# ============================================================
# 接口 5.5：下载原始 Word 文件
# ============================================================
@router.get("/analyze/{analysis_id}/download-original")
def download_original_resume(
    analysis_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis or not analysis.original_file_path:
        raise HTTPException(status_code=404, detail="原始文件记录不存在")

    original_path = Path(analysis.original_file_path)
    if not original_path.exists():
        raise HTTPException(status_code=404, detail="原始文件已被清除")

    return FileResponse(
        path=str(original_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"原版_{analysis.original_filename}",
    )


# ============================================================
# 接口 6：获取当前用户历史分析列表
# ============================================================
@router.get("/history")
def get_resume_history(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.owner_id == user_id)
        .order_by(ResumeAnalysis.created_at.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "original_filename": a.original_filename,
            "job_target": a.job_target,
            "job_match_score": a.job_match_score,
            "status": a.status,
            "created_at": a.created_at.isoformat() + "Z" if a.created_at else None,
        }
        for a in analyses
    ]


# ============================================================
# 接口 7：获取某次历史分析的完整内容（只读回顾）
# ============================================================
@router.get("/analyze/{analysis_id}")
def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # 复用进度接口逻辑，只是这里用于历史回顾
    return get_analysis_progress(analysis_id, db, user_id)


# ============================================================
# 接口 8：取消并删除某次分析
# ============================================================
@router.delete("/analyze/{analysis_id}")
def delete_resume_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.owner_id == user_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="记录不存在或无权操作")

    try:
        if analysis.original_file_path and os.path.exists(analysis.original_file_path):
            os.remove(analysis.original_file_path)
        if analysis.output_file_path and os.path.exists(analysis.output_file_path):
            os.remove(analysis.output_file_path)
            # 同时尝试清理相关的双模副本
            if "_full.docx" in analysis.output_file_path:
                content_path = analysis.output_file_path.replace("_full.docx", "_content.docx")
                if os.path.exists(content_path):
                    os.remove(content_path)
    except Exception as e:
        print(f"删除物理文件异常: {e}")

    db.delete(analysis)
    db.commit()
    return {"ok": True, "msg": "记录已删除"}
