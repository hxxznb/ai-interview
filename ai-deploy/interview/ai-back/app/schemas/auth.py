from pydantic import BaseModel



class LoginRequest(BaseModel):
    account: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
