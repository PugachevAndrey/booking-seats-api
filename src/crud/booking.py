from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.booking import Booking


class CRUDBooking(CRUDBase[Booking]):
    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.user_id == user_id, Booking.is_active.is_(True))
            .order_by(Booking.booking_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_cafe_and_date(
        self,
        session: AsyncSession,
        cafe_id: UUID,
        booking_date: date,
    ) -> list[Booking]:
        """Все брони кафе на конкретную дату.

        Используется сервисом для проверки пересечений —
        сам CRUD ничего не валидирует.
        """
        stmt = select(Booking).where(
            Booking.cafe_id == cafe_id,
            Booking.booking_date == booking_date,
            Booking.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_date(
        self,
        session: AsyncSession,
        user_id: UUID,
        booking_date: date,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.user_id == user_id,
            Booking.booking_date == booking_date,
            Booking.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_relations(
        self, session: AsyncSession, obj_id: UUID
    ) -> Booking | None:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Booking)
            .where(Booking.id == obj_id, Booking.is_active.is_(True))
            .options(
                selectinload(Booking.tables),
                selectinload(Booking.slots),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


booking_crud = CRUDBooking(Booking)
