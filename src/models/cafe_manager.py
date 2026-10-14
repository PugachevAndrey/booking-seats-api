"""Модель управляющих кафе."""

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class CafeManager(Base):
    """Управляющие кафе."""

    __tablename__ = 'cafe_managers'

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        comment='ID пользователя',
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
