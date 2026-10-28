"""Модель стола."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.base_model import Base
from shared.models.cafe import Cafe


class Table(Base):
    """Модель стола."""

    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id'),
        comment='ID кафе',
    )
    cafe: Mapped[Cafe] = relationship(Cafe, lazy='selectin')
    description: Mapped[str | None] = mapped_column(
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
        CheckConstraint(
            'seat_number > 0',
            name='ck_tables_seat_number_is_positive',
        ),
    )
