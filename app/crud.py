from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models
import schemas

# Инициализация для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_login(db: Session, login: str):
    """Получить пользователя по логину"""
    return db.query(models.User).filter(models.User.login == login).first()

def get_user(db: Session, user_id: int):
    """Получить пользователя по ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Получить список пользователей"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Создать нового пользователя"""
    # Хешируем пароль
    hashed_password = pwd_context.hash(user.password)
    
    # Создаем объект пользователя
    db_user = models.User(
        login=user.login,
        password_hash=hashed_password
    )
    
    # Добавляем в базу данных
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def verify_password(plain_password: str, hashed_password: str):
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, login: str, password: str):
    """Аутентификация пользователя"""
    user = get_user_by_login(db, login)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_users_count(db: Session):
    """Получить количество пользователей"""
    return db.query(models.User).count()