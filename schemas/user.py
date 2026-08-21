from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario unico")
    email: EmailStr = Field(..., description="Correo electronico valido")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Contrasena con minimo 6 caracteres")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="Rol del usuario (user o admin)")


class UserLogin(BaseModel):
    username: str = Field(..., description="Nombre de usuario o correo electronico")
    password: str = Field(..., description="Contrasena del usuario")


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
