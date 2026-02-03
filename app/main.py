from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging
import os

from database import get_db, engine, Base
import crud
import schemas
import models

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Контекстный менеджер для lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при запуске приложения
    logger.info("🚀 Запуск приложения...")
    logger.info("✅ База данных инициализирована")
    yield
    # Код, который выполняется при остановке приложения
    logger.info("🛑 Остановка приложения...")

# Создаем приложение
app = FastAPI(
    title="Authentication App with SQLAlchemy",
    version="2.0.0",
    lifespan=lifespan
)

# Получаем абсолютный путь к директории со static файлами
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# Проверяем существование директорий
logger.info(f"📁 Текущая директория: {current_dir}")
logger.info(f"📁 Директория static: {static_dir}")
logger.info(f"📁 Директория templates: {templates_dir}")

if not os.path.exists(static_dir):
    logger.warning(f"⚠️ Директория static не найдена: {static_dir}")
    os.makedirs(static_dir, exist_ok=True)
    logger.info(f"✅ Создана директория static: {static_dir}")

if not os.path.exists(templates_dir):
    logger.warning(f"⚠️ Директория templates не найдена: {templates_dir}")
    os.makedirs(templates_dir, exist_ok=True)
    logger.info(f"✅ Создана директория templates: {templates_dir}")

# Настройка шаблонов и статических файлов с абсолютными путями
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Главная страница с формой
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Страница входа
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Страница успешного входа
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request, 
    login: str = None,
    message: str = None
):
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "login": login,
            "message": message
        }
    )

# Обработка формы регистрации
@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Проверяем ввод
        if not login or not password:
            raise HTTPException(status_code=400, detail="Логин и пароль обязательны")
        
        if len(password) < 3:
            raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 3 символа")
        
        # Проверяем, существует ли пользователь
        existing_user = crud.get_user_by_login(db, login)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        
        # Создаем объект пользователя
        user_data = schemas.UserCreate(login=login, password=password)
        
        # Сохраняем пользователя в базе данных
        user = crud.create_user(db, user_data)
        
        # Логируем успешную регистрацию
        logger.info(f"✅ Пользователь '{login}' успешно зарегистрирован с ID: {user.id}")
        
        # Возвращаем страницу с подтверждением
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "login": login,
                "user_id": user.id,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
    except HTTPException as e:
        logger.warning(f"⚠️ Ошибка регистрации: {e.detail}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": e.detail
            }
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"Произошла ошибка: {str(e)}"
            }
        )

# Обработка формы входа
@app.post("/login", response_class=HTMLResponse)
async def login_user_form(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Аутентифицируем пользователя
        user = crud.authenticate_user(db, login, password)
        if not user:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        logger.info(f"✅ Пользователь '{login}' успешно вошел в систему")
        
        # Перенаправляем на dashboard с параметром логина
        return RedirectResponse(
            url=f"/dashboard?login={login}&message=Вы успешно вошли в систему", 
            status_code=303
        )
        
    except HTTPException as e:
        logger.warning(f"⚠️ Ошибка входа: {e.detail}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": e.detail,
                "login": login
            }
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": f"Произошла ошибка: {str(e)}",
                "login": login
            }
        )

# Выход из системы
@app.get("/logout", response_class=HTMLResponse)
async def logout_user(request: Request):
    return templates.TemplateResponse(
        "logout.html",
        {
            "request": request,
            "message": "Вы успешно вышли из системы"
        }
    )

# API: Получить всех пользователей
@app.get("/api/users", response_model=schemas.UserList)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей"""
    users = crud.get_users(db, skip=skip, limit=limit)
    count = crud.get_users_count(db)
    
    return {
        "users": users,
        "count": count
    }

# API: Получить пользователя по ID
@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Получить пользователя по ID"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# Веб-страница: Просмотр всех пользователей
@app.get("/users", response_class=HTMLResponse)
async def view_users_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Страница со списком всех пользователей"""
    users = crud.get_users(db)
    count = crud.get_users_count(db)
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users,
            "count": count
        }
    )

# API для аутентификации (JSON)
@app.post("/api/auth/login")
async def login_user_api(
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Аутентификация пользователя"""
    user = crud.authenticate_user(db, login, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль"
        )
    
    return {
        "message": "Аутентификация успешна",
        "user_id": user.id,
        "login": user.login
    }

# Проверка состояния базы данных
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Проверка работоспособности приложения и БД"""
    try:
        # Пробуем выполнить простой запрос к БД
        count = crud.get_users_count(db)
        
        return {
            "status": "healthy",
            "database": "connected",
            "user_count": count,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка проверки здоровья: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Информация о приложении
@app.get("/api/info")
async def app_info():
    return {
        "app": "Authentication App with SQLAlchemy",
        "description": "Приложение для регистрации пользователей с использованием SQLAlchemy ORM",
        "version": "2.0.0",
        "features": [
            "Регистрация пользователей с валидацией",
            "Хеширование паролей с помощью bcrypt",
            "SQLAlchemy ORM для работы с базой данных",
            "Поддержка SQLite/PostgreSQL/MySQL",
            "REST API для управления пользователями",
            "Веб-интерфейс на HTML/Jinja2"
        ],
        "endpoints": {
            "web": ["/", "/login", "/dashboard", "/logout", "/users"],
            "api": ["/api/users", "/api/users/{id}", "/api/auth/login", "/api/health", "/api/info"]
        }
    }