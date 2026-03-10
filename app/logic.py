from passlib.context import CryptContext
from schemas.schemas import LoginRequest
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from fastapi import Depends, Security, Request, HTTPException, status
import models.models as models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# перенести bearer в конфиг
access_security = JwtAccessBearer(secret_key="ya_lublu_maxim_technology")


def verify_password(plain_password: str, hashed_password: str):
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(creds: JwtAuthorizationCredentials = Security(access_security)):
    return creds.subject

def login_req(user: LoginRequest = Depends(get_current_user)) -> LoginRequest:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="некорректный ввод логина или пароля",
            headers={"WWW-Authenticate": "Bearer"}
            )
    
def get_client_ip(request: Request) -> str:
    """Получить IP адрес клиента"""
    return request.client.host if request.client else "unknown"