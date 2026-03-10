from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.database import get_db
from app.crud import get_user_by_login, create_user, create_user_activity
from app.logic import verify_password
from schemas.schemas import UserCreate, LoginRequest
import logging
from app.logic import get_client_ip, access_security

router = APIRouter(prefix="/user", tags=["user"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Страница входа
@router.get("/login")
async def login_page(request: Request, login_request: LoginRequest, db: Session = Depends(get_db)):
    user_in_db = get_user_by_login(db, login_request.login)
    if user_in_db == None or verify_password(login_request.password, user_in_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="некорректный ввод логина или пароля",
            headers={"WWW-Authenticate": "Bearer"}
            )
    return access_security.create_access_token(subject=user_in_db.model_dump())

# Страница регистрации
@router.post("/register")
async def register_page(request: Request, user_data: UserCreate):
    existing_user = get_user_by_login(user_data.login())
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    else:
        new_user = create_user(user_data)
    return request, new_user.id

# Дашборд пользователя
@router.get("/dashboard")
async def dashboard_page(
    request: Request,
    login: str = None,
    message: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Логируем активность
    create_user_activity(
        db, user.id, "view_dashboard",
        ip_address=get_client_ip(request)
    )
    
    return request, user, message

# Выход из системы
@router.get("/logout")
async def logout_user(request: Request, login: str = None, db: Session = Depends(get_db)):
    if login:
        user = get_user_by_login(db, login)
        if user:
            create_user_activity(
                db, user.id, "logout",
                ip_address=get_client_ip(request)
            )
    
    return request, "Вы успешно вышли из системы"
