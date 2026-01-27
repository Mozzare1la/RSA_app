from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional

# Схема для создания пользователя
class UserCreate(BaseModel):
    login: str
    password: str
    
    @validator('login')
    def validate_login(cls, v):
        if len(v) < 3:
            raise ValueError('Логин должен содержать минимум 3 символа')
        if len(v) > 50:
            raise ValueError('Логин не должен превышать 50 символов')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 3:
            raise ValueError('Пароль должен содержать минимум 3 символа')
        return v

# Схема для ответа с пользователем
class UserResponse(BaseModel):
    id: int
    login: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схема для списка пользователей
class UserList(BaseModel):
    users: list[UserResponse]
    count: int