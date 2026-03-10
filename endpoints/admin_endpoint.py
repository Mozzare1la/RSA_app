from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.database import get_db
import app.crud as crud
import logging
from app.logic import get_client_ip

router = APIRouter(prefix="/admin", tags=["admin"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## связать с бизнес логикой


@router.get("/")
async def admin_panel(
    request: Request,
    login: str = None,
    message: str = None,
    db: Session = Depends(get_db),
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)

    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/login", status_code=303)

    # Получаем статистику
    stats = crud.get_admin_stats(db)

    return request, user, stats, message


# Список пользователей для админа
@router.get("/users")
async def admin_users_page(
    request: Request, login: str = None, db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)

    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/login", status_code=303)

    # Получаем всех пользователей
    users = crud.get_users(db)

    return request, user, users


# Активность пользователей
@router.get("/activity")
async def admin_activity_page(
    request: Request, login: str = None, db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)

    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/login", status_code=303)

    # Получаем всю активность
    activities = crud.get_all_activities(db, limit=200)

    return request, user, activities

# Выход из системы
@router.get("/logout")
async def logout_user(request: Request, login: str = None, db: Session = Depends(get_db)):
    if login:
        user = crud.get_user_by_login(db, login)
        if user:
            crud.create_user_activity(
                db, user.id, "logout",
                ip_address=get_client_ip(request)
            )
    
    return request, "Вы успешно вышли из системы"

