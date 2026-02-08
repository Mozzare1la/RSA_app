from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging
import os
from typing import Optional
import json
from datetime import datetime

# Импортируем RSA модули
import RSA_fast

from database import get_db, engine, Base
import crud
import schemas
import models

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы в базе данных - УДАЛЯЕМ СТАРЫЕ И СОЗДАЕМ НОВЫЕ
Base.metadata.drop_all(bind=engine)  # Удаляем старые таблицы
Base.metadata.create_all(bind=engine)  # Создаем новые с обновленной схемой
logger.info("✅ Таблицы базы данных пересозданы с новой схемой")

# Контекстный менеджер для lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при запуске приложения
    logger.info("🚀 Запуск приложения...")
    logger.info("✅ База данных инициализирована")
    
    # Создаем администратора по умолчанию, если его нет
    db = next(get_db())
    try:
        admin = crud.get_user_by_login(db, "admin")
        if not admin:
            admin_data = schemas.UserCreate(
                login="admin",
                password="admin123",
                role="admin"
            )
            crud.create_user(db, admin_data)
            logger.info("✅ Создан администратор по умолчанию (admin/admin123)")
            
        # Создаем тестового пользователя
        test_user = crud.get_user_by_login(db, "user")
        if not test_user:
            user_data = schemas.UserCreate(
                login="user",
                password="user123",
                role="user"
            )
            crud.create_user(db, user_data)
            logger.info("✅ Создан тестовый пользователь (user/user123)")
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания пользователей: {e}")
    finally:
        db.close()
    
    yield
    # Код, который выполняется при остановке приложения
    logger.info("🛑 Остановка приложения...")

# Создаем приложение
app = FastAPI(
    title="RSA Cryptography System with Admin Panel",
    version="2.0.0",
    lifespan=lifespan
)

# Получаем абсолютный путь к директориям
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# Настройка шаблонов и статических файлов с абсолютными путями
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ========== Вспомогательные функции ==========
def get_client_ip(request: Request) -> str:
    """Получить IP адрес клиента"""
    return request.client.host if request.client else "unknown"

def check_admin_access(user: models.User):
    """Проверить права администратора"""
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )

# ========== ВЕБ-СТРАНИЦЫ ==========

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Страница входа
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Страница регистрации
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Веб-страница: Просмотр всех пользователей (для всех)
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

# ========== Пользовательские страницы ==========

# Дашборд пользователя
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    login: str = None,
    message: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Логируем активность
    crud.create_user_activity(
        db, user.id, "view_dashboard",
        ip_address=get_client_ip(request)
    )
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "message": message
        }
    )

# Страница генерации ключей
@app.get("/keys", response_class=HTMLResponse)
async def keys_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Получаем ключи пользователя
    keys = crud.get_user_keypairs(db, user.id)
    
    return templates.TemplateResponse(
        "keys.html",
        {
            "request": request,
            "user": user,
            "keys": keys
        }
    )

# Страница шифрования
@app.get("/encrypt", response_class=HTMLResponse)
async def encrypt_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Получаем ключи пользователя
    keys = crud.get_user_keypairs(db, user.id)
    
    return templates.TemplateResponse(
        "encrypt.html",
        {
            "request": request,
            "user": user,
            "keys": keys
        }
    )

# Страница расшифрования
@app.get("/decrypt", response_class=HTMLResponse)
async def decrypt_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Получаем ключи пользователя
    keys = crud.get_user_keypairs(db, user.id)
    
    return templates.TemplateResponse(
        "decrypt.html",
        {
            "request": request,
            "user": user,
            "keys": keys
        }
    )

# История операций
@app.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Получаем операции пользователя
    operations = crud.get_user_operations(db, user.id, limit=100)
    
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user": user,
            "operations": operations
        }
    )

# ========== Административные страницы ==========

# Админ панель
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    login: str = None,
    message: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/dashboard?login={login}", status_code=303)
    
    # Получаем статистику
    stats = crud.get_admin_stats(db)
    
    return templates.TemplateResponse(
        "admin_panel.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "message": message
        }
    )

# Список пользователей для админа
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/dashboard?login={login}", status_code=303)
    
    # Получаем всех пользователей
    users = crud.get_users(db)
    
    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "user": user,
            "users": users
        }
    )

# Активность пользователей
@app.get("/admin/activity", response_class=HTMLResponse)
async def admin_activity_page(
    request: Request,
    login: str = None,
    db: Session = Depends(get_db)
):
    if not login:
        return RedirectResponse(url="/login", status_code=303)
    
    user = crud.get_user_by_login(db, login)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем права администратора
    if user.role != "admin":
        return RedirectResponse(url="/dashboard?login={login}", status_code=303)
    
    # Получаем всю активность
    activities = crud.get_all_activities(db, limit=200)
    
    return templates.TemplateResponse(
        "admin_activity.html",
        {
            "request": request,
            "user": user,
            "activities": activities
        }
    )

# ========== АВТОРИЗАЦИЯ ==========

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
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Аккаунт отключен")
        
        # Логируем вход
        crud.create_user_activity(
            db, user.id, "login",
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"✅ Пользователь '{login}' успешно вошел в систему")
        
        # Перенаправляем в зависимости от роли
        if user.role == "admin":
            return RedirectResponse(
                url=f"/admin?login={login}&message=Добро пожаловать в админ-панель",
                status_code=303
            )
        else:
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

# Обработка формы регистрации
@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    db: Session = Depends(get_db)
):
    try:
        # Проверяем ввод
        if not login or not password:
            raise HTTPException(status_code=400, detail="Логин и пароль обязательны")
        
        if len(password) < 3:
            raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 3 символа")
        
        if role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Некорректная роль")
        
        # Проверяем, существует ли пользователь
        existing_user = crud.get_user_by_login(db, login)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        
        # Создаем объект пользователя
        user_data = schemas.UserCreate(login=login, password=password, role=role)
        
        # Сохраняем пользователя в базе данных
        user = crud.create_user(db, user_data)
        
        # Логируем регистрацию
        crud.create_user_activity(
            db, user.id, "register",
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"✅ Пользователь '{login}' успешно зарегистрирован с ID: {user.id}")
        
        # Возвращаем страницу с подтверждением
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "login": login,
                "user_id": user.id,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "role": user.role
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

# Выход из системы
@app.get("/logout", response_class=HTMLResponse)
async def logout_user(request: Request, login: str = None, db: Session = Depends(get_db)):
    if login:
        user = crud.get_user_by_login(db, login)
        if user:
            crud.create_user_activity(
                db, user.id, "logout",
                ip_address=get_client_ip(request)
            )
    
    return templates.TemplateResponse(
        "logout.html",
        {
            "request": request,
            "message": "Вы успешно вышли из системы"
        }
    )

# ========== RSA ОПЕРАЦИИ (API) ==========

# Генерация RSA ключей
@app.post("/api/rsa/generate")
async def generate_rsa_keys(
    request: Request,
    login: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_login(db, login)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        # Генерируем ключи
        pub_key, priv_key = RSA_fast.RSA_key_gen_fast()
        
        # Сохраняем в базу
        keypair = crud.create_rsa_keypair(
            db,
            user.id,
            json.dumps(pub_key),
            json.dumps(priv_key)
        )
        
        # Логируем активность
        crud.create_user_activity(
            db, user.id, "key_generation",
            f"Сгенерированы ключи ID: {keypair.id}",
            get_client_ip(request)
        )
        
        return {
            "success": True,
            "message": "Ключи успешно сгенерированы",
            "key_id": keypair.id,
            "public_key": pub_key,
            "private_key": priv_key
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации ключей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации ключей: {str(e)}")

# Шифрование
@app.post("/api/rsa/encrypt")
async def rsa_encrypt(
    request: Request,
    login: str = Form(...),
    text: str = Form(...),
    key_id: int = Form(None),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_login(db, login)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        # Получаем ключ
        if key_id:
            keypair = crud.get_keypair(db, key_id)
            if not keypair or keypair.user_id != user.id:
                raise HTTPException(status_code=403, detail="Доступ к ключу запрещен")
            pub_key = json.loads(keypair.public_key)
        else:
            # Генерируем временные ключи
            pub_key, _ = RSA_fast.RSA_key_gen_fast()
            key_id = None
        
        # Шифруем текст
        cipher = RSA_fast.RSA_encrypt_fast(text, pub_key)
        
        # Сохраняем операцию
        operation = crud.create_rsa_operation(
            db, user.id, "encrypt",
            text, json.dumps(cipher), key_id
        )
        
        # Логируем активность
        crud.create_user_activity(
            db, user.id, "encrypt",
            f"Зашифрован текст длиной {len(text)} символов",
            get_client_ip(request)
        )
        
        return {
            "success": True,
            "message": "Текст успешно зашифрован",
            "operation_id": operation.id,
            "cipher": cipher,
            "public_key": pub_key
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка шифрования: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка шифрования: {str(e)}")

# Расшифрование
@app.post("/api/rsa/decrypt")
async def rsa_decrypt(
    request: Request,
    login: str = Form(...),
    cipher: str = Form(...),
    key_id: int = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_login(db, login)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        # Получаем ключ
        keypair = crud.get_keypair(db, key_id)
        if not keypair or keypair.user_id != user.id:
            raise HTTPException(status_code=403, detail="Доступ к ключу запрещен")
        
        priv_key = json.loads(keypair.private_key)
        
        # Парсим cipher
        cipher_list = json.loads(cipher)
        
        # Расшифровываем
        text = RSA_fast.RSA_decrypt_fast(cipher_list, priv_key)
        text_str = ''.join(text)
        
        # Сохраняем операцию
        operation = crud.create_rsa_operation(
            db, user.id, "decrypt",
            json.dumps(cipher_list), text_str, key_id
        )
        
        # Логируем активность
        crud.create_user_activity(
            db, user.id, "decrypt",
            f"Расшифрован текст длиной {len(text_str)} символов",
            get_client_ip(request)
        )
        
        return {
            "success": True,
            "message": "Текст успешно расшифрован",
            "operation_id": operation.id,
            "text": text_str
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка расшифрования: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расшифрования: {str(e)}")

# ========== ДОПОЛНИТЕЛЬНЫЕ СТРАНИЦЫ ==========

# Страница "О нас"
@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

# Страница помощи
@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

# ========== API для проверки состояния ==========

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
        "app": "RSA Cryptography System",
        "description": "Система шифрования RSA с админ-панелью",
        "version": "2.0.0",
        "features": [
            "Регистрация и аутентификация пользователей",
            "Генерация RSA ключей",
            "Шифрование и расшифрование текста",
            "История операций",
            "Админ-панель для управления пользователями",
            "Отслеживание активности пользователей"
        ],
        "endpoints": {
            "web": ["/", "/login", "/register", "/dashboard", "/keys", "/encrypt", "/decrypt", "/history", "/admin", "/logout"],
            "api": ["/api/rsa/generate", "/api/rsa/encrypt", "/api/rsa/decrypt", "/api/health", "/api/info"]
        }
    }