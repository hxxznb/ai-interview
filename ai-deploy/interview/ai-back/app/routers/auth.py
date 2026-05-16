import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db, pwd_context, get_current_user_id
from app.models.user import User
from app.schemas.auth import LoginRequest, ChangePasswordRequest

router = APIRouter()


@router.post("/api/login")
def login_or_register(request: LoginRequest, db: Session = Depends(get_db)):
    # --- 安全校验：限制账号不少于8位，密码不少于10位 ---
    if len(request.account) < 8:
        raise HTTPException(status_code=400, detail="账号长度不能少于 8 位")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="密码长度不能少于 8 位")

    user = db.query(User).filter(User.account == request.account).first()
    if not user:
        hashed_password = pwd_context.hash(request.password)
        new_user = User(account=request.account, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        if not pwd_context.verify(request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="账号或密码错误")

    payload = {
        "sub": str(user.id),
        "account": user.account,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=settings.JWT_EXPIRE_DAYS)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"message": "登录成功", "token": token, "account": user.account}


@router.post("/api/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="两次新密码输入不一致")

    # --- 新增：安全校验 ---
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码长度不能少于 8 位")
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not pwd_context.verify(request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码验证失败")

    user.password_hash = pwd_context.hash(request.new_password)
    db.commit()

    return {"message": "密码修改成功"}
