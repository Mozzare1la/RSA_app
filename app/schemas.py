from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any

# Схема для создания пользователя
class UserCreate(BaseModel):
    login: str
    password: str
    role: str = "user"  # По умолчанию обычный пользователь
    
    @field_validator('login')
    def validate_login(cls, v):
        if len(v) < 3:
            raise ValueError('Логин должен содержать минимум 3 символа')
        if len(v) > 50:
            raise ValueError('Логин не должен превышать 50 символов')
        return v
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 3:
            raise ValueError('Пароль должен содержать минимум 3 символа')
        return v
    
    @field_validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'admin']:
            raise ValueError('Роль должна быть "user" или "admin"')
        return v

# Схема для ответа с пользователем
class UserResponse(BaseModel):
    id: int
    login: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

# Схема для списка пользователей
class UserList(BaseModel):
    users: List[UserResponse]
    count: int

# Схема для RSA ключей
class RSAKeyPairCreate(BaseModel):
    public_key: str
    private_key: str

class RSAKeyPairResponse(BaseModel):
    id: int
    user_id: int
    public_key: str
    private_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схема для RSA операций
class RSAOperationCreate(BaseModel):
    operation_type: str
    input_data: str
    output_data: str
    key_id: Optional[int] = None

class RSAOperationResponse(BaseModel):
    id: int
    user_id: int
    operation_type: str
    input_data: str
    output_data: str
    key_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схема для активности пользователя
class UserActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Схема для входа
class LoginRequest(BaseModel):
    login: str
    password: str

# Схема для административной информации
class AdminUserInfo(BaseModel):
    user: UserResponse
    activity_count: int
    last_activity: Optional[datetime]
    keys_count: int
    operations_count: int