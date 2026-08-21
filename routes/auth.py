from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
)
from models.user import User, UserRole
from schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario en el sistema.",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya se encuentra registrado",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electronico ya se encuentra registrado",
        )

    # Hash password and save user
    hashed_pwd = get_password_hash(user_in.password)
    user_role=UserRole.USER

    if settings.DEBUG:
        user_role = user_in.role if user_in.role else UserRole.USER


    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión (Form / OAuth2)",
    description="Autentica las credenciales del usuario y retorna un token JWT Bearer compatible con OpenAPI / Swagger.",
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Search by username or email
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (usuario/email o contraseña no válidos)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario se encuentra inactiva",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/login/json",
    response_model=Token,
    summary="Iniciar sesión (JSON payload)",
    description="Autentica las credenciales del usuario mediante un cuerpo JSON.",
)
def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            (User.username == credentials.username)
            | (User.email == credentials.username)
        )
        .first()
    )
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (usuario/email o contraseña no válidos)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta de usuario se encuentra inactiva",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario autenticado",
    description="Retorna la información del usuario autenticado actualmente.",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/admin/users",
    response_model=List[UserResponse],
    summary="Listar usuarios (Solo administradores)",
    description="Endpoint protegido exclusivo para administradores que retorna la lista de todos los usuarios.",
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_current_admin),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users
