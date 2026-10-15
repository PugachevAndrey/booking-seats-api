"""Модель стола."""

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base


class Table(Base):
    """Модель стола."""

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment='Описание стола',
    )
    seat_number: Mapped[int] = mapped_column(
        Integer,
        comment='Номер сидения',
    )

    __table_args__ = (
        Index(
            'ix_tables_cafe_id',
            'cafe_id',
        ),
    )
