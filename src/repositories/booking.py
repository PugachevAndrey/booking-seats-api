from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase
from shared.models.booking import Booking


class CRUDBooking(CRUDBase[Booking]):
    """CRUD для бронирований."""

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> list[Booking]:
        """Получить брони пользователя."""
        result = await session.execute(
            select(Booking).where(Booking.user_id == user_id),
        )
        return list(result.scalars().all())

    async def get_by_cafe_and_date(
        self,
        session: AsyncSession,
        cafe_id: int,
        booking_date: date,
    ) -> list[Booking]:
        """Получить брони кафе на конкретную дату."""
        result = await session.execute(
            select(Booking).where(
                Booking.cafe_id == cafe_id,
                Booking.booking_date == booking_date,
            ),
        )
        return list(result.scalars().all())

    async def get_by_user_and_date(
        self,
        session: AsyncSession,
        user_id: int,
        booking_date: date,
    ) -> list[Booking]:
        """Получить брони пользователя на конкретную дату."""
        result = await session.execute(
            select(Booking).where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
            ),
        )
        return list(result.scalars().all())


booking_crud = CRUDBooking(Booking)
