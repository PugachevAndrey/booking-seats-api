from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException
from pydantic import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.slot import slot_crud
from src.repositories.user import user_crud
from src.schemas.base import AuthSchema
from src.schemas.booking import BookingCreate
from src.schemas.slot import TimeSlotUpdate
from src.schemas.user import UserCreate, UserUpdate


async def validate_user_create_unique(
    user_data: UserCreate,
    session: AsyncSession,
) -> None:
    """Проверка уникальности email, phone, tg_id при создании пользователя."""
    if user_data.email is not MISSING:
        user = await user_crud.get_by_attribute('email', user_data.email, session)
        if user is not None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой email уже существует.',
            )
    if user_data.phone is not MISSING:
        user = await user_crud.get_by_attribute('phone', user_data.phone, session)
        if user is not None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой phone уже существует.',
            )
    if user_data.tg_id is not MISSING:
        user = await user_crud.get_by_attribute('tg_id', user_data.tg_id, session)
        if user is not None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой tg_id уже существует.',
            )


async def validate_user_update_unique(
    user: User,
    user_data: UserUpdate,
    session: AsyncSession,
) -> None:
    """Проверка уникальности email, phone, tg_id при изменении пользователя."""
    if user_data.email is not MISSING:
        current_user = await user_crud.get_by_attribute('email', user_data.email, session)
        if current_user is not None and current_user.id != user.id:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой email уже существует.',
            )
    if user_data.phone is not MISSING:
        current_user = await user_crud.get_by_attribute('phone', user_data.phone, session)
        if current_user is not None and current_user.id != user.id:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой phone уже существует.',
            )
    if user_data.tg_id is not MISSING:
        current_user = await user_crud.get_by_attribute('tg_id', user_data.tg_id, session)
        if current_user is not None and current_user.id != user.id:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Такой tg_id уже существует.',
            )


async def validate_slot_update(
    slot_data: TimeSlotUpdate,
    slot_id: int,
    session: AsyncSession,
) -> None:
    """Проверка времени начала и окончания бронирования."""
    current_slot = await slot_crud.get(obj_id=slot_id, session=session)
    if current_slot.start_time is not MISSING:
        end_time = current_slot.end_time
        if end_time <= slot_data.start_time:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Время начала не может быть позже времени окончания.',
            )
    if current_slot.end_time is not MISSING:
        start_time = current_slot.start_time
        if start_time >= slot_data.end_time:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Время окончания не может быть раньше времени начала.',
            )


async def validate_login(
    auth_data: AuthSchema,
    session: AsyncSession,
) -> None:
    """Проверка логина и пароля."""
    user = await user_crud.get_by_login(login=auth_data.login, session=session)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='В поле login введите email или phone.',
        )
    if not user.check_password(password=auth_data.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Неверные имя пользователя и пароль.',
        )


async def validate_booking(
    booking_data: BookingCreate,
    session: AsyncSession,
) -> None:
    """Проверка времени бронирования для пользователя."""
    for slot in booking_data.tables_slots:
        slot = await slot_crud.get(obj_id=slot.slot_id, session=session)
        if slot is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Такой слот не существует.',
            )
        booking_time = datetime.combine(
            booking_data.booking_date,
            slot.start_time,
        )
        if booking_time < datetime.now():
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Нельзя забронировать прошедшее время.',
            )
