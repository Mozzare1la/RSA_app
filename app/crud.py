from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models
import schemas
from datetime import datetime
from typing import List, Optional

# Инициализация для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========== Пользователи ==========
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
        password_hash=hashed_password,
        role=user.role
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
    
    # Обновляем время последнего входа
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    
    return user

def get_users_count(db: Session):
    """Получить количество пользователей"""
    return db.query(models.User).count()

def get_users_by_role(db: Session, role: str):
    """Получить пользователей по роли"""
    return db.query(models.User).filter(models.User.role == role).all()

# ========== RSA Ключи ==========
def create_rsa_keypair(db: Session, user_id: int, public_key: str, private_key: str):
    """Создать пару RSA ключей"""
    db_keypair = models.RSAKeyPair(
        user_id=user_id,
        public_key=public_key,
        private_key=private_key
    )
    
    db.add(db_keypair)
    db.commit()
    db.refresh(db_keypair)
    
    return db_keypair

def get_user_keypairs(db: Session, user_id: int):
    """Получить ключи пользователя"""
    return db.query(models.RSAKeyPair).filter(models.RSAKeyPair.user_id == user_id).all()

def get_keypair(db: Session, key_id: int):
    """Получить ключ по ID"""
    return db.query(models.RSAKeyPair).filter(models.RSAKeyPair.id == key_id).first()

def delete_keypair(db: Session, key_id: int, user_id: int):
    """Удалить ключ (только владелец)"""
    keypair = db.query(models.RSAKeyPair).filter(
        models.RSAKeyPair.id == key_id,
        models.RSAKeyPair.user_id == user_id
    ).first()
    
    if keypair:
        db.delete(keypair)
        db.commit()
        return True
    return False

# ========== RSA Операции ==========
def create_rsa_operation(db: Session, user_id: int, operation_type: str, 
                         input_data: str, output_data: str, key_id: Optional[int] = None):
    """Создать запись об операции RSA"""
    db_operation = models.RSAOperation(
        user_id=user_id,
        operation_type=operation_type,
        input_data=input_data,
        output_data=output_data,
        key_id=key_id
    )
    
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    
    return db_operation

def get_user_operations(db: Session, user_id: int, limit: int = 50):
    """Получить операции пользователя"""
    return db.query(models.RSAOperation).filter(
        models.RSAOperation.user_id == user_id
    ).order_by(models.RSAOperation.created_at.desc()).limit(limit).all()

def get_all_operations(db: Session, skip: int = 0, limit: int = 100):
    """Получить все операции (для админа)"""
    return db.query(models.RSAOperation).offset(skip).limit(limit).all()

# ========== Активность пользователей ==========
def create_user_activity(db: Session, user_id: int, activity_type: str, 
                         details: Optional[str] = None, ip_address: Optional[str] = None):
    """Создать запись об активности пользователя"""
    db_activity = models.UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        details=details,
        ip_address=ip_address
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    return db_activity

def get_user_activities(db: Session, user_id: int, limit: int = 50):
    """Получить активность пользователя"""
    return db.query(models.UserActivity).filter(
        models.UserActivity.user_id == user_id
    ).order_by(models.UserActivity.created_at.desc()).limit(limit).all()

def get_all_activities(db: Session, skip: int = 0, limit: int = 100):
    """Получить всю активность (для админа)"""
    return db.query(models.UserActivity).offset(skip).limit(limit).all()

# ========== Административные функции ==========
def get_admin_stats(db: Session):
    """Получить статистику для админа"""
    stats = {
        "total_users": db.query(models.User).count(),
        "active_users": db.query(models.User).filter(models.User.is_active == True).count(),
        "admins_count": db.query(models.User).filter(models.User.role == "admin").count(),
        "total_keys": db.query(models.RSAKeyPair).count(),
        "total_operations": db.query(models.RSAOperation).count(),
        "total_activities": db.query(models.UserActivity).count(),
    }
    return stats

def get_user_detailed_info(db: Session, user_id: int):
    """Получить детальную информацию о пользователе"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    activity_count = db.query(models.UserActivity).filter(
        models.UserActivity.user_id == user_id
    ).count()
    
    keys_count = db.query(models.RSAKeyPair).filter(
        models.RSAKeyPair.user_id == user_id
    ).count()
    
    operations_count = db.query(models.RSAOperation).filter(
        models.RSAOperation.user_id == user_id
    ).count()
    
    last_activity = db.query(models.UserActivity).filter(
        models.UserActivity.user_id == user_id
    ).order_by(models.UserActivity.created_at.desc()).first()
    
    return {
        "user": user,
        "activity_count": activity_count,
        "last_activity": last_activity.created_at if last_activity else None,
        "keys_count": keys_count,
        "operations_count": operations_count
    }