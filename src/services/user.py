from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

from .access import ROLE_ADMIN, ensure_admin, ensure_staff
from .errors import ConflictError, NotFoundError


async def get_user(session: AsyncSession, user_id: int) -> User:
    """Возвращает активного пользователя по ID."""
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise NotFoundError(f'Пользователь {user_id} не найден.')
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Возвращает пользователя по e-mail."""
    result = await session.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_users(
    session: AsyncSession,
    actor_role: str,
    actor_cafe_id: int | None,
) -> list[User]:
    """Возвращает список активных пользователей согласно роли."""
    ensure_staff(actor_role)
    query = select(User).where(User.is_active.is_(True))
    if actor_role != ROLE_ADMIN and actor_cafe_id is not None:
        query = query.where(User.cafe_id == actor_cafe_id)
    result = await session.execute(query.order_by(User.id))
    return list(result.scalars().all())


async def _ensure_unique(
    session: AsyncSession,
    email: str,
    phone: str,
    tg_id: str,
    exclude_user_id: int | None = None,
) -> None:
    """Проверяет уникальность email, phone и tg_id."""
    query = select(User).where(
        or_(
            User.email == email,
            User.phone == phone,
            User.tg_id == tg_id,
        )
    )
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    result = await session.execute(query)
    if result.first() is not None:
        raise ConflictError('Пользователь с такими данными уже существует.')


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    phone: str,
    tg_id: str,
    password_hash: str,
    role: str,
    cafe_id: int,
) -> User:
    """Создаёт нового пользователя."""
    await _ensure_unique(session, email, phone, tg_id)

    user = User(
        username=username,
        email=email,
        phone=phone,
        tg_id=tg_id,
        password_hash=password_hash,
        role=role,
        cafe_id=cafe_id,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update_user(
    session: AsyncSession,
    actor_id: int,
    actor_role: str,
    user_id: int,
    **fields: object,
) -> User:
    """Обновляет поля пользователя с проверкой прав и уникальности."""
    if actor_id != user_id:
        ensure_admin(actor_role)

    user = await get_user(session, user_id)

    if any(key in fields for key in ('email', 'phone', 'tg_id')):
        await _ensure_unique(
            session,
            fields.get('email', user.email),
            fields.get('phone', user.phone),
            fields.get('tg_id', user.tg_id),
            exclude_user_id=user_id,
        )

    allowed = {'username', 'email', 'phone', 'tg_id', 'password_hash', 'role', 'cafe_id'}
    for name, value in fields.items():
        if name in allowed:
            setattr(user, name, value)
    await session.flush()
    await session.refresh(user)
    return user


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
    user.is_active = False
    await session.flush()
