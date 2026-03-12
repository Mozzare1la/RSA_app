from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.database import get_db
import app.crud as crud
from app.logic import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/")
async def admin_panel(
    request: Request,
    admin = Depends(require_admin),
    db: Session = Depends(get_db),
):

    # Получаем статистику
    stats = crud.get_admin_stats(db)

    return {"user": admin, "stats": stats}


# Список пользователей для админа
@router.get("/users")
async def admin_users_page(
    request: Request,
    admin = Depends(require_admin),
    db: Session = Depends(get_db),
):

    # Получаем всех пользователей
    users = crud.get_users(db)

    return {"user": admin, "users": users}


# Активность пользователей
@router.get("/activity")
async def admin_activity_page(
    request: Request,
    admin = Depends(require_admin),
    db: Session = Depends(get_db),
):

    # Получаем всю активность
    activities = crud.get_all_activities(db, limit=200)

    return {"user": admin, "activities": activities}

# Выход из системы
@router.post("/logout")
async def logout_user(request: Request, db: Session = Depends(get_db)):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
