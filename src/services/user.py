from typing import Any

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import user_crud
from schemas.user import UserUpdate
from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.models.cafe_manager import CafeManager
from shared.models.user import User
from validators import (
    ensure_text_not_blank,
    validate_role,
    validate_role_change,
    validate_user_fields,
)

from .access import ROLES, ROLE_ADMIN, ROLE_USER, ensure_admin, ensure_staff

USER_EDITABLE_FIELDS = frozenset(
    {'username', 'email', 'phone', 'tg_id', 'password', 'role'},
)
UNIQUE_FIELDS = frozenset({'email', 'phone', 'tg_id'})
PROFILE_FIELDS = frozenset({'username', 'email', 'phone', 'tg_id'})
STAFF_EDITABLE_FIELDS = USER_EDITABLE_FIELDS | {'is_active'}

UNIQUE_CONFLICT_MESSAGE = 'Пользователь с такими данными уже существует.'


class _UserCreate(BaseModel):
    """Внутренняя схема создания пользователя."""

    username: str
    email: str | None = None
    phone: str | None = None
    tg_id: str | None = None
    password_hash: str
    role: str


async def get_user(session: AsyncSession, user_id: int) -> User:
    """Возвращает активного пользователя по ID."""
    user = await user_crud.get(session=session, obj_id=user_id)
    if user is None or not user.is_active:
        raise NotFoundError(f'Пользователь {user_id} не найден.')
    return user


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """Возвращает активного пользователя по e-mail."""
    user = await user_crud.get_by_attribute(
        session=session,
        attribute='email',
        value=email,
    )
    if user is None or not user.is_active:
        return None
    return user


async def get_users(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
) -> list[User]:
    """Возвращает список активных пользователей согласно роли."""
    ensure_staff(actor_role)

    if actor_role == ROLE_ADMIN:
        users = await user_crud.get_multi(session=session)
        return sorted(
            (user for user in users if user.is_active),
            key=lambda user: user.id,
        )

    if actor_cafe_id is None:
        return []

    result = await session.execute(
        select(User)
        .join(CafeManager, CafeManager.user_id == User.id)
        .where(
            User.is_active.is_(True),
            CafeManager.cafe_id == actor_cafe_id,
        )
        .order_by(User.id),
    )
    return list(result.scalars().all())


async def _ensure_unique(
    session: AsyncSession,
    email: str | None,
    phone: str | None,
    tg_id: str | None,
    exclude_user_id: int | None = None,
) -> None:
    """Проверяет уникальность заполненных email, phone и tg_id."""
    conditions = []
    if email is not None:
        conditions.append(User.email == email)
    if phone is not None:
        conditions.append(User.phone == phone)
    if tg_id is not None:
        conditions.append(User.tg_id == tg_id)
    if not conditions:
        return

    query = select(User.id).where(or_(*conditions))
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    result = await session.execute(query)
    if result.first() is not None:
        raise ConflictError(UNIQUE_CONFLICT_MESSAGE)


async def create_user(
    session: AsyncSession,
    username: str,
    email: str | None,
    phone: str | None,
    tg_id: str | None,
    password: str,
    role: str = ROLE_USER,
) -> User:
    """Создаёт нового пользователя."""
    validate_user_fields(username, email, phone, tg_id)
    if email is None and phone is None:
        raise ValidationError('Нужен email или телефон.')
    validate_role(role, ROLES)
    ensure_text_not_blank(password, 'Пароль')

    await _ensure_unique(session, email, phone, tg_id)

    try:
        return await user_crud.create(
            session=session,
            obj_in=_UserCreate(
                username=username,
                email=email,
                phone=phone,
                tg_id=tg_id,
                password_hash=User.hash_password(password),
                role=role,
            ),
        )
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(UNIQUE_CONFLICT_MESSAGE) from exc


async def update_user(  # noqa: C901
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    user_id: int,
    **fields: Any,
) -> User:
    """Обновляет поля пользователя с проверкой прав и уникальности."""
    is_self = actor_id == user_id
    is_admin = actor_role == ROLE_ADMIN

    user = await get_user(session, user_id)

    if not is_self and not is_admin:
        ensure_admin(actor_role)

    allowed = STAFF_EDITABLE_FIELDS if is_admin else USER_EDITABLE_FIELDS
    unknown = set(fields) - allowed
    if unknown:
        raise ValidationError(
            f'Поля нельзя изменить: {", ".join(sorted(unknown))}.',
        )

    if fields.get('is_active') is False and is_self:
        raise ValidationError('Нельзя деактивировать себя.')

    if 'role' in fields:
        validate_role_change(
            actor_id,
            user_id,
            actor_role,
            ROLE_ADMIN,
        )
        validate_role(fields['role'], ROLES)

    if PROFILE_FIELDS & fields.keys():
        merged = {
            'username': fields.get('username', user.username),
            'email': fields.get('email', user.email),
            'phone': fields.get('phone', user.phone),
            'tg_id': fields.get('tg_id', user.tg_id),
        }
        validate_user_fields(**merged)
        if merged['email'] is None and merged['phone'] is None:
            raise ValidationError('Нужен email или телефон.')

    if UNIQUE_FIELDS & fields.keys():
        await _ensure_unique(
            session,
            fields.get('email', user.email),
            fields.get('phone', user.phone),
            fields.get('tg_id', user.tg_id),
            exclude_user_id=user_id,
        )

    if 'password' in fields:
        user.set_password(fields.pop('password'))

    if not fields:
        await session.flush()
        return user

    try:
        return await user_crud.update(
            session=session,
            db_obj=user,
            obj_in=UserUpdate(**fields),
        )
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(UNIQUE_CONFLICT_MESSAGE) from exc


async def delete_user(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    user_id: int,
) -> None:
    """Мягко удаляет пользователя."""
    if actor_id != user_id:
        ensure_admin(actor_role)
    user = await get_user(session, user_id)

    await user_crud.update(
        session=session,
        db_obj=user,
        obj_in=UserUpdate(is_active=False),
    )
