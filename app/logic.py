from passlib.context import CryptContext
from schemas.schemas import LoginRequest
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from fastapi import Depends, Security, Request, HTTPException, status
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
import crud

security = HTTPBearer()

async def get_current_user_from_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        # Декодируем токен
        payload = jwt.decode(
            token, 
            "ya_lublu_maxim_technology", 
            algorithms=["HS256"]
        )
        login = payload.get("sub", {}).get("login")
        if not login:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен"
            )
        
        # Получаем пользователя из БД
        user = crud.get_user_by_login(db, login)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден"
            )
        
        # Сохраняем пользователя в request.state для использования в других функциях
        request.state.user = user
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )

async def require_admin(user = Depends(get_current_user_from_token)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return user

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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