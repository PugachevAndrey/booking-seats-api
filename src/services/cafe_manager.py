from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe_manager import CafeManager
from models.user import User
from repositories.cafe import cafe_crud

from .access import ensure_admin
from core.errors import ConflictError, NotFoundError


async def _ensure_cafe_exists(
    session: AsyncSession,
    cafe_id: int,
) -> None:
    """Проверяет существование активного кафе."""
    cafe = await cafe_crud.get(session=session, obj_id=cafe_id)
    if cafe is None or not cafe.is_active:
        raise NotFoundError(f'Кафе {cafe_id} не найдено.')


async def _ensure_users_exist(
    session: AsyncSession,
    manager_ids: list[int],
) -> None:
    """Проверяет, что все активные пользователи существуют."""
    if not manager_ids:
        return
    result = await session.execute(
        select(User.id).where(
            User.id.in_(manager_ids),
            User.is_active.is_(True),
        ),
    )
    found = set(result.scalars().all())
    missing = set(manager_ids) - found
    if missing:
        raise ConflictError(
            f'Пользователи не найдены: {sorted(missing)}.',
        )


async def _ensure_managers_free(
    session: AsyncSession,
    manager_ids: list[int],
    cafe_id: int,
) -> None:
    """Проверяет, что менеджеры не привязаны к другому кафе."""
    if not manager_ids:
        return
    result = await session.execute(
        select(CafeManager.user_id).where(
            CafeManager.user_id.in_(manager_ids),
            CafeManager.cafe_id != cafe_id,
        ),
    )
    busy = result.scalars().all()
    if busy:
        raise ConflictError(
            f'Менеджеры уже привязаны к другому кафе: {sorted(busy)}.',
        )


async def _drop_cafe_links(
    session: AsyncSession,
    cafe_id: int,
) -> None:
    """Удаляет все связи кафе с менеджерами."""
    result = await session.execute(
        select(CafeManager).where(CafeManager.cafe_id == cafe_id),
    )
    for link in result.scalars().all():
        await session.delete(link)
    await session.flush()


async def get_cafe_managers(
    session: AsyncSession,
    cafe_id: int,
) -> list[CafeManager]:
    """Возвращает связи кафе с менеджерами."""
    await _ensure_cafe_exists(session, cafe_id)
    result = await session.execute(
        select(CafeManager).where(CafeManager.cafe_id == cafe_id).order_by(CafeManager.user_id),
    )
    return list(result.scalars().all())


async def get_cafe_manager_ids(
    session: AsyncSession,
    cafe_id: int,
) -> list[int]:
    """Возвращает идентификаторы менеджеров кафе."""
    await _ensure_cafe_exists(session, cafe_id)
    result = await session.execute(
        select(CafeManager.user_id).where(CafeManager.cafe_id == cafe_id).order_by(CafeManager.user_id),
    )
    return list(result.scalars().all())


async def get_manager_cafe_id(
    session: AsyncSession,
    user_id: int,
) -> int | None:
    """Возвращает кафе, к которому привязан менеджер."""
    result = await session.execute(
        select(CafeManager.cafe_id).where(
            CafeManager.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def sync_cafe_managers(
    session: AsyncSession,
    cafe_id: int,
    manager_ids: list[int] | None,
) -> None:
    """Синхронизирует набор менеджеров кафе."""
    if manager_ids is None:
        return

    await _ensure_cafe_exists(session, cafe_id)
    await _ensure_users_exist(session, manager_ids)
    await _ensure_managers_free(session, manager_ids, cafe_id)

    await _drop_cafe_links(session, cafe_id)

    for user_id in dict.fromkeys(manager_ids):
        session.add(CafeManager(user_id=user_id, cafe_id=cafe_id))
    await session.flush()


async def add_cafe_manager(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
    user_id: int,
) -> CafeManager:
    """Привязывает менеджера к кафе."""
    ensure_admin(actor_role)
    await _ensure_cafe_exists(session, cafe_id)
    await _ensure_users_exist(session, [user_id])
    await _ensure_managers_free(session, [user_id], cafe_id)

    link = CafeManager(user_id=user_id, cafe_id=cafe_id)
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link


async def remove_cafe_manager(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
    user_id: int,
) -> None:
    """Отвязывает менеджера от кафе."""
    ensure_admin(actor_role)
    result = await session.execute(
        select(CafeManager).where(
            CafeManager.user_id == user_id,
            CafeManager.cafe_id == cafe_id,
        ),
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError(
            f'Менеджер {user_id} не привязан к кафе {cafe_id}.',
        )
    await session.delete(link)
    await session.flush()


async def delete_cafe_managers(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
) -> None:
    """Удаляет все связи кафе с менеджерами."""
    ensure_admin(actor_role)
    await _ensure_cafe_exists(session, cafe_id)
    await _drop_cafe_links(session, cafe_id)
