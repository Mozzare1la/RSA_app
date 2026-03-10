from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging
import os

from database import get_db, engine, Base
import crud
import schemas.schemas as schemas
from endpoints.admin_endpoint import router as admin_router
from endpoints.RSA_endpoint import router as rsa_router
from endpoints.user_endpoint import router as user_router


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
    title="RSA Cryptography System",
    version="3",
    lifespan=lifespan
)

# Получаем абсолютный путь к директориям
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# Настройка шаблонов и статических файлов с абсолютными путями
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ========== Подключаем роутеры ==========

app.include_router(admin_router)
app.include_router(rsa_router)
app.include_router(user_router)

# ========== Вспомогательные страницы ==========

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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