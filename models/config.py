from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from core.database import Base


class SystemConfig(Base):
    """
    Modelo de base de datos para almacenar configuraciones dinámicas del sistema
    gestionadas en tiempo de ejecución por administradores.
    """
    __tablename__ = "system_configs"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"
