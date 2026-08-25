from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class UserToken(Base):
    """
    Modelo de base de datos para almacenar Tokens de API de usuarios.
    Solo almacena el hash SHA-256 del token, nunca el token en texto plano.
    """
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False, index=True)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    prefix = Column(String(32), nullable=False)
    scopes = Column(String(255), default="all", nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relación con el modelo User
    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        UniqueConstraint("user_id", "label", name="uq_user_token_label"),
    )

    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, label='{self.label}', prefix='{self.prefix}', revoked={self.revoked})>"
