import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.user import User, UserRole
from models.token import UserToken
from schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de autenticacion",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception


def generate_user_api_key(prefix: str = "myelina_") -> Tuple[str, str, str]:
    """
    Genera un nuevo API Key seguro para el usuario.
    Retorna:
        - raw_key: La clave completa en texto plano que verá el usuario solo una vez (ej: myelina_abc123...)
        - key_hash: El hash SHA-256 que se guardará en la base de datos
        - key_prefix: Prefijo recortado para mostrar en listados seguros (ej: myelina_abc123...)
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{random_part}"
    key_hash = hash_api_key(raw_key)
    key_prefix = f"{raw_key[:12]}..."
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Calcula el hash SHA-256 de un API key en texto plano."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to retrieve the authenticated user.
    Soporta de forma unificada:
    1. Tokens de API con prefijo 'myelina_' (o hash registrado en la tabla user_tokens)
    2. Tokens JWT Bearer estándar
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de autenticación",
        headers={"WWW-Authenticate": "Bearer"},
    )

    clean_token = token.strip()

    # 1. Si es un API Key con prefijo 'myelina_'
    if clean_token.startswith("myelina_"):
        key_hash = hash_api_key(clean_token)
        token_record = db.query(UserToken).filter(UserToken.key_hash == key_hash).first()
        if not token_record:
            raise credentials_exception

        if token_record.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token de API ha sido revocado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_record.expires_at:
            expires = token_record.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="El token de API ha expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo",
            )

        # Actualizar last_used_at
        token_record.last_used_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()

        return user

    # 2. Intentar validar como JWT estándar
    try:
        token_data = decode_access_token(clean_token)
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo",
            )
        return user
    except HTTPException:
        # 3. Fallback: verificar si es una API Key registrada sin prefijo tradicional
        key_hash = hash_api_key(clean_token)
        token_record = db.query(UserToken).filter(UserToken.key_hash == key_hash).first()
        if token_record and not token_record.revoked:
            if token_record.expires_at:
                expires = token_record.expires_at
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="El token de API ha expirado",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            user = db.query(User).filter(User.id == token_record.user_id).first()
            if user and user.is_active:
                token_record.last_used_at = datetime.now(timezone.utc)
                try:
                    db.commit()
                except Exception:
                    db.rollback()
                return user

        raise credentials_exception


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency to ensure the authenticated user has administrator privileges."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol de administrador.",
        )
    return current_user
