"""Бизнес-логика пользователей."""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import user_crud
from schemas.user import UserUpdate
from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.models.user import User
from validators import ensure_text_not_blank

from .access import ROLES, ROLE_ADMIN, ROLE_USER, ensure_admin, ensure_staff

USER_EDITABLE_FIELDS = frozenset(
    {'username', 'email', 'phone', 'tg_id', 'password', 'role'},
)
PROFILE_FIELDS = frozenset({'username', 'email', 'phone', 'tg_id'})
STAFF_EDITABLE_FIELDS = USER_EDITABLE_FIELDS | {'is_active'}

UNIQUE_CONFLICT_MESSAGE = 'Пользователь с такими данными уже существует.'
UNIQUE_VIOLATION_CODE = '23505'  # PostgreSQL: unique_violation


def _is_unique_violation(exc: IntegrityError) -> bool:
    """Проверяет, что IntegrityError вызвана нарушением UNIQUE."""
    return getattr(getattr(exc, 'orig', None), 'pgcode', None) == (
        UNIQUE_VIOLATION_CODE
    )


def _conflict_from_integrity() -> ConflictError:
    """Превращает нарушение UNIQUE в доменный конфликт."""
    return ConflictError(UNIQUE_CONFLICT_MESSAGE)


async def get_user(session: AsyncSession, user_id: int) -> User:
    """Возвращает пользователя по ID."""
    user = await user_crud.get(session=session, obj_id=user_id)
    if user is None:
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

    users = await user_crud.get_by_cafe_id(
        session=session,
        cafe_id=actor_cafe_id,
    )
    return sorted(users, key=lambda user: user.id)


def _validate_role_change(
    actor_id: int,
    user_id: int,
    actor_role: str,
    new_role: str,
) -> None:
    """Проверяет права на смену роли и допустимость роли."""
    if actor_id == user_id:
        raise ValidationError('Нельзя менять собственную роль.')
    ensure_admin(actor_role)
    if new_role not in ROLES:
        raise ValidationError(f'Недопустимая роль: {new_role}.')


async def create_user(
    session: AsyncSession,
    username: str,
    email: str | None,
    phone: str | None,
    tg_id: str | None,
    password: str,
    role: str = ROLE_USER,
) -> User:
    """Создаёт нового пользователя.

    Длины полей и формат email/phone проверяет схема UserCreate.
    Уникальность email/phone/tg_id обеспечивает БД: нарушение
    превращается в ConflictError (409).
    """
    if email is None and phone is None:
        raise ValidationError('Нужен email или телефон.')
    if role not in ROLES:
        raise ValidationError(f'Недопустимая роль: {role}.')
    ensure_text_not_blank(password, 'Пароль')

    try:
        return await user_crud.create_from_dict(
            session=session,
            data={
                'username': username,
                'email': email,
                'phone': phone,
                'tg_id': tg_id,
                'password_hash': User.hash_password(password),
                'role': role,
            },
        )
    except IntegrityError as exc:
        await session.rollback()
        if _is_unique_violation(exc):
            raise _conflict_from_integrity() from exc
        raise


def _validate_change_permission(
    is_self: bool,
    is_admin: bool,
    actor_role: str,
    fields: dict[str, Any],
    user: User,
) -> None:
    """Проверяет права на изменение и корректность набора полей."""
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

    if PROFILE_FIELDS & fields.keys():
        merged_email = fields.get('email', user.email)
        merged_phone = fields.get('phone', user.phone)
        if merged_email is None and merged_phone is None:
            raise ValidationError('Нужен email или телефон.')


async def update_user(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    user_id: int,
    **fields: Any,
) -> User:
    """Обновляет поля пользователя с проверкой прав.

    Уникальность email/phone/tg_id обеспечивает БД.
    """
    is_self = actor_id == user_id
    is_admin = actor_role == ROLE_ADMIN

    user = await get_user(session, user_id)

    _validate_change_permission(
        is_self, is_admin, actor_role, fields, user,
    )

    if 'role' in fields:
        _validate_role_change(actor_id, user_id, actor_role, fields['role'])

    if 'password' in fields:
        password = fields.pop('password')
        ensure_text_not_blank(password, 'Пароль')
        user.set_password(password)

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
        if _is_unique_violation(exc):
            raise _conflict_from_integrity() from exc
        raise


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
