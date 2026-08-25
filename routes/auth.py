from datetime import datetime, timedelta, timezone
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
    generate_user_api_key,
)
from models.user import User, UserRole
from models.token import UserToken
from schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)
from schemas.token import (
    UserTokenCreate,
    UserTokenCreatedResponse,
    UserTokenInfoResponse,
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


@router.post(
    "/tokens",
    response_model=UserTokenCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Token / API Key para el usuario",
    description=(
        "Genera un nuevo token de API con prefijo 'myelina_' vinculado a la cuenta del usuario. "
        "El servidor calcula y almacena únicamente el hash SHA-256 en la base de datos, "
        "y retorna el token en texto plano UNA SOLA VEZ en la respuesta. "
        "No se permite repetir la misma etiqueta ('label') para la cuenta del mismo usuario."
    ),
)
def create_user_token(
    token_in: UserTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verificar que el usuario no tenga ya un token con el mismo label
    existing_token = (
        db.query(UserToken)
        .filter(
            UserToken.user_id == current_user.id,
            UserToken.label == token_in.label,
        )
        .first()
    )
    if existing_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un token con la etiqueta '{token_in.label}' para tu cuenta.",
        )

    # Calcular expiración si aplica
    expires_at = None
    if token_in.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=token_in.expires_in_days)

    # Generar API Key (raw_key para el cliente una sola vez, hash para la DB)
    raw_key, key_hash, prefix = generate_user_api_key(prefix="myelina_")

    # Guardar en base de datos
    new_token = UserToken(
        user_id=current_user.id,
        label=token_in.label,
        key_hash=key_hash,
        prefix=prefix,
        scopes=token_in.scopes or "all",
        revoked=False,
        expires_at=expires_at,
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    return UserTokenCreatedResponse(
        id=new_token.id,
        label=new_token.label,
        token=raw_key,
        prefix=new_token.prefix,
        scopes=new_token.scopes,
        revoked=new_token.revoked,
        created_at=new_token.created_at,
        expires_at=new_token.expires_at,
        message="Token generado con éxito. Cópialo y guárdalo en un lugar seguro; no podrás volver a verlo.",
    )


@router.get(
    "/tokens",
    response_model=List[UserTokenInfoResponse],
    summary="Listar Tokens / API Keys del usuario",
    description="Retorna la lista de todos los tokens creados por el usuario autenticado (mostrando solo metadatos y prefijo seguro).",
)
def list_user_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tokens = (
        db.query(UserToken)
        .filter(UserToken.user_id == current_user.id)
        .order_by(UserToken.created_at.desc())
        .all()
    )
    return tokens


@router.post(
    "/tokens/{token_id}/revoke",
    summary="Revocar Token / API Key",
    description="Marca un token específico como revocado para invalidar inmediatamente su acceso.",
)
def revoke_user_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_record = (
        db.query(UserToken)
        .filter(
            UserToken.id == token_id,
            UserToken.user_id == current_user.id,
        )
        .first()
    )
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token no encontrado o no pertenece a tu cuenta.",
        )

    token_record.revoked = True
    db.commit()
    return {"message": f"Token '{token_record.label}' revocado exitosamente.", "revoked": True}


@router.delete(
    "/tokens/{token_id}",
    summary="Eliminar Token / API Key",
    description="Elimina permanentemente un token de la base de datos.",
)
def delete_user_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_record = (
        db.query(UserToken)
        .filter(
            UserToken.id == token_id,
            UserToken.user_id == current_user.id,
        )
        .first()
    )
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token no encontrado o no pertenece a tu cuenta.",
        )

    db.delete(token_record)
    db.commit()
    return {"message": f"Token '{token_record.label}' eliminado exitosamente."}
