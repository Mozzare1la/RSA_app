from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
import app.crud as crud
from app.logic import require_admin
import os

# Настройка шаблонов
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):

    try:
        # Получаем статистику
        stats = crud.get_admin_stats(db)

        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "user": admin,
                "stats": stats,
                "active_tab": "dashboard",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка загрузки админ-панели: {str(e)}"
        )


# Список пользователей для админа
@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):

    try:
        # Получаем всех пользователей
        users = crud.get_users(db)

        return templates.TemplateResponse(
            "admin_users.html",
            {"request": request, "user": admin, "users": users, "active_tab": "users"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка загрузки пользователей: {str(e)}"
        )


# Активность пользователей
@router.get("/activity", response_class=HTMLResponse)
async def admin_activity_page(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):

    try:
        # Получаем всю активность
        activities = crud.get_all_activities(db, limit=200)

        return templates.TemplateResponse(
            "admin_activity.html",
            {
                "request": request,
                "user": admin,
                "activities": activities,
                "active_tab": "activity",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка загрузки активности: {str(e)}"
        )


# Выход из системы
@router.post("/logout")
async def logout_user(request: Request, db: Session = Depends(get_db)):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
