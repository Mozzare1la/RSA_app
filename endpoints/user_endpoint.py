from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import get_db
from app.crud import get_user_by_login, create_user, create_user_activity
from app.logic import verify_password
from schemas.schemas import UserCreate, LoginRequest
import logging
from app.logic import get_client_ip, access_security, get_current_user_from_token

router = APIRouter(prefix="/user", tags=["user"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/login")
async def login_page(
    request: Request, 
    login_request: LoginRequest, 
    db: Session = Depends(get_db)
):
    user_in_db = get_user_by_login(db, login_request.login)
    if not user_in_db or not verify_password(login_request.password, user_in_db.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="некорректный ввод логина или пароля",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Создаем токен
    access_token = access_security.create_access_token(
        subject={"id": user_in_db.id, "login": user_in_db.login, "role": user_in_db.role}
    )
    
    # Создаем ответ и устанавливаем cookie с токеном
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
        secure=False,  # В продакшне True для HTTPS
        samesite="lax"
    )
    
    # Логируем активность
    create_user_activity(
        db, user_in_db.id, "login", 
        ip_address=get_client_ip(request)
    )
    
    return response

# Страница регистрации
@router.post("/register")
async def register_page(request: Request, user_data: UserCreate):
    existing_user = get_user_by_login(user_data.login())
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    else:
        new_user = create_user(user_data)
    return {"request" : request, "new_user" : new_user.id}

# Дашборд пользователя
@router.get("/dashboard")
async def dashboard_page(
    request: Request,
     user = Depends(get_current_user_from_token),
    message: str = None,
    db: Session = Depends(get_db)
):
    if user == None:
        return RedirectResponse(url="/login", status_code=303)
    
    # Логируем активность
    create_user_activity(
        db, user.id, "view_dashboard",
        ip_address=get_client_ip(request)
    )
    
    return {"request" : request, "user" : user}

# Выход из системы
@router.post("/logout")
async def logout_user(request: Request, db: Session = Depends(get_db)):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response