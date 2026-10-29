"""Модель кафе."""

import uuid

from sqlalchemy import UUID, ForeignKey, String, Text, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base
from shared.models.cafe_manager import CafeManager
from shared.models.user import User


class Cafe(Base):
    """Модель кафе."""

    name: Mapped[str] = mapped_column(
        String(255),
        comment='Название кафе',
    )
    address: Mapped[str] = mapped_column(
        String(500),
        comment='Адрес кафе',
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        comment='Телефон кафе',
    )
    description: Mapped[str | None] = mapped_column(
        Text(),
        comment='Описание кафе',
    )
    photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey('media.id', ondelete='SET NULL'),
        comment='ID фотографии',
    )
    managers: Mapped[list[User]] = relationship(
        'User',
        secondary='cafe_managers',
        lazy='selectin',
        secondaryjoin=and_(
            CafeManager.user_id == User.id,
            CafeManager.is_active.is_(True),
        ),
        viewonly=True,
    )
