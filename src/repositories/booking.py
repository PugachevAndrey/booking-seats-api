"""Репозиторий бронирований."""

from datetime import date, time

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import CRUDBase
from shared.models.booking import Booking
from shared.models.booking_tables_slot import BookingTablesSlot
from shared.models.slot import Slot


class CRUDBooking(CRUDBase[Booking]):
    """CRUD для бронирований."""

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: int,
        booking_date: date | None = None,
    ) -> list[Booking]:
        """Получить брони пользователя, опционально — на дату."""
        query = select(Booking).where(Booking.user_id == user_id)
        if booking_date is not None:
            query = query.where(Booking.booking_date == booking_date)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
        booking_date: date | None = None,
    ) -> list[Booking]:
        """Получить брони кафе, опционально — на дату."""
        query = select(Booking).where(Booking.cafe_id == cafe_id)
        if booking_date is not None:
            query = query.where(Booking.booking_date == booking_date)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_cafe_and_date(
        self,
        session: AsyncSession,
        cafe_id: int,
        booking_date: date,
    ) -> list[Booking]:
        """Получить брони кафе на конкретную дату."""
        return await self.get_by_cafe(
            session=session,
            cafe_id=cafe_id,
            booking_date=booking_date,
        )

    async def get_by_user_and_date(
        self,
        session: AsyncSession,
        user_id: int,
        booking_date: date,
    ) -> list[Booking]:
        """Получить брони пользователя на конкретную дату."""
        return await self.get_by_user(
            session=session,
            user_id=user_id,
            booking_date=booking_date,
        )

    async def get_active_links(
        self,
        session: AsyncSession,
        booking_id: int,
    ) -> list[BookingTablesSlot]:
        """Получить активные связки столов и слотов брони."""
        result = await session.execute(
            select(BookingTablesSlot)
            .where(
                BookingTablesSlot.booking_id == booking_id,
                BookingTablesSlot.is_active.is_(True),
            )
            .order_by(BookingTablesSlot.id),
        )
        return list(result.scalars().all())

    async def create_links(
        self,
        session: AsyncSession,
        booking_id: int,
        pairs: list[tuple[int, int]],
    ) -> list[BookingTablesSlot]:
        """Создать связки столов и слотов для брони."""
        if not pairs:
            return []
        links = [
            BookingTablesSlot(
                booking_id=booking_id,
                table_id=table_id,
                slot_id=slot_id,
            )
            for table_id, slot_id in pairs
        ]
        session.add_all(links)
        await session.flush()
        return links

    async def deactivate_links(
        self,
        session: AsyncSession,
        booking_id: int,
    ) -> None:
        """Деактивировать все связки брони (без физического удаления)."""
        links = await self.get_active_links(
            session=session,
            booking_id=booking_id,
        )
        for link in links:
            link.is_active = False
        await session.flush()

    async def replace_links(
        self,
        session: AsyncSession,
        booking_id: int,
        pairs: list[tuple[int, int]],
    ) -> None:
        """Заменить связки столов и слотов, деактивировав старые."""
        await self.deactivate_links(session=session, booking_id=booking_id)
        await self.create_links(
            session=session,
            booking_id=booking_id,
            pairs=pairs,
        )

    async def is_slot_busy(
        self,
        session: AsyncSession,
        table_id: int,
        start_time: time,
        end_time: time,
        booking_date: date,
        statuses: tuple[str, ...],
        exclude_booking_id: int | None = None,
    ) -> bool:
        """Проверить, занят ли стол в слоте на дату."""
        query = (
            select(BookingTablesSlot)
            .join(Booking, Booking.id == BookingTablesSlot.booking_id)
            .join(Slot, Slot.id == BookingTablesSlot.slot_id)
            .where(
                BookingTablesSlot.table_id == table_id,
                BookingTablesSlot.is_active.is_(True),
                Booking.is_active.is_(True),
                Booking.status.in_(statuses),
                Booking.booking_date == booking_date,
                Slot.start_time < end_time,
                Slot.end_time > start_time,
            )
        )
        if exclude_booking_id is not None:
            query = query.where(Booking.id != exclude_booking_id)
        result = await session.execute(query)
        return result.first() is not None

    async def exists_for_user_in_cafe(
        self,
        session: AsyncSession,
        user_id: int,
        cafe_id: int,
    ) -> bool:
        """Проверить, есть ли у пользователя брони в кафе."""
        result = await session.execute(
            select(
                exists().where(
                    Booking.user_id == user_id,
                    Booking.cafe_id == cafe_id,
                    Booking.is_active.is_(True),
                ),
            ),
        )
        return result.scalar_one()


booking_crud = CRUDBooking(Booking)
