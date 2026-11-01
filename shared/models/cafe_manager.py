"""Модель управляющих кафе."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base

if TYPE_CHECKING:
    from shared.models.cafe import Cafe
    from shared.models.user import User


class CafeManager(Base):
    """Управляющие кафе."""

    __tablename__ = 'cafe_managers'

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        unique=True,
        comment='ID пользователя',
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )

    user: Mapped["User"] = relationship(lazy="selectin")
    cafe: Mapped["Cafe"] = relationship(lazy="selectin")
