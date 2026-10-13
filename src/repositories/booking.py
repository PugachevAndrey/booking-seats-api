from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.booking import Booking
from repositories.base import CRUDBase


class CRUDBooking(CRUDBase[Booking]):
    """CRUD для бронирований."""

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        """Брони конкретного пользователя."""
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
        """Все брони кафе на конкретную дату."""
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
        """Брони пользователя на конкретную дату."""
        stmt = select(Booking).where(
            Booking.user_id == user_id,
            Booking.booking_date == booking_date,
            Booking.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


booking_crud = CRUDBooking(Booking)
