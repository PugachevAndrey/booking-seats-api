"""Бизнес-логика управления менеджерами кафе."""

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.cafe import cafe_crud
from repositories.cafe_manager import cafe_manager_crud
from repositories.user import user_crud
from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.models.cafe_manager import CafeManager

from .access import ensure_admin


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
    found = await cafe_manager_crud.get_existing_user_ids(
        session=session,
        user_ids=manager_ids,
    )
    missing = set(manager_ids) - found
    if missing:
        raise ConflictError(
            f'Пользователи не найдены: {sorted(missing)}.',
        )


async def _ensure_manager_role(
    session: AsyncSession,
    manager_ids: list[int],
) -> None:
    """Проверяет, что у пользователей роль менеджер."""
    if not manager_ids:
        return
    found = await user_crud.get_many(
        session=session,
        obj_ids=manager_ids,
    )
    found_users = {user.id for user in found}
    missing = set(manager_ids) - found_users
    if missing:
        raise ConflictError(
            f'Пользователи не найдены: {sorted(missing)}.',
        )
    for user in found:
        if user.role != 'MANAGER':
            raise ValidationError(
                f'Пользователь id={user.id} не является менеджером.',
            )


async def _ensure_managers_free(
    session: AsyncSession,
    manager_ids: list[int],
    cafe_id: int,
) -> None:
    """Проверяет, что менеджеры не привязаны к другому кафе."""
    if not manager_ids:
        return
    busy = await cafe_manager_crud.get_busy_user_ids(
        session=session,
        user_ids=manager_ids,
        exclude_cafe_id=cafe_id,
    )
    if busy:
        raise ConflictError(
            f'Менеджеры уже привязаны к другому кафе: {sorted(busy)}.',
        )


async def _deactivate_link(
    session: AsyncSession,
    link: CafeManager,
) -> None:
    """Помечает связь менеджера с кафе неактивной."""
    link.is_active = False
    await session.flush()


async def _attach_manager(
    session: AsyncSession,
    cafe_id: int,
    user_id: int,
) -> CafeManager:
    """Привязывает менеджера к кафе, переиспользуя неактивную связь.

    У CafeManager.user_id стоит unique=True, поэтому новую строку
    создаём только если ни одной связи у пользователя ещё нет.
    Существующую неактивную связь реактивируем и переносим в кафе.
    """
    link = await cafe_manager_crud.get_link_by_user(
        session=session,
        user_id=user_id,
    )
    if link is not None:
        link.cafe_id = cafe_id
        link.is_active = True
        await session.flush()
        return link

    return await cafe_manager_crud.create_from_dict(
        session=session,
        data={'cafe_id': cafe_id, 'user_id': user_id},
    )


async def get_manager_cafe_id(
    session: AsyncSession,
    user_id: int,
) -> int | None:
    """Возвращает кафе активной привязки менеджера."""
    return await cafe_manager_crud.get_cafe_id_by_user(
        session=session,
        user_id=user_id,
    )


async def sync_cafe_managers(
    session: AsyncSession,
    cafe_id: int,
    manager_ids: list[int] | None,
) -> None:
    """Приводит состав менеджеров кафе к заданному без удаления записей.

    Лишние связи деактивируются, недостающие создаются или
    реактивируются. Строки из БД не удаляются.
    """
    if manager_ids is None:
        return

    target = set(dict.fromkeys(manager_ids))

    await _ensure_cafe_exists(session, cafe_id)
    await _ensure_users_exist(session, list(target))
    await _ensure_managers_free(session, list(target), cafe_id)
    await _ensure_manager_role(session, list(target))

    current = set(
        await cafe_manager_crud.get_manager_ids_by_cafe(
            session=session,
            cafe_id=cafe_id,
        ),
    )

    for user_id in current - target:
        link = await cafe_manager_crud.get_link(
            session=session,
            cafe_id=cafe_id,
            user_id=user_id,
        )
        if link is not None:
            await _deactivate_link(session, link)

    for user_id in target - current:
        await _attach_manager(session, cafe_id, user_id)


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
    await _ensure_manager_role(session, [user_id])

    existing = await cafe_manager_crud.get_link(
        session=session,
        cafe_id=cafe_id,
        user_id=user_id,
    )
    if existing is not None:
        raise ConflictError(
            f'Менеджер {user_id} уже привязан к кафе {cafe_id}.',
        )

    await _ensure_managers_free(session, [user_id], cafe_id)
    return await _attach_manager(session, cafe_id, user_id)


async def remove_cafe_manager(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
    user_id: int,
) -> None:
    """Отвязывает менеджера от кафе без удаления строки."""
    ensure_admin(actor_role)
    link = await cafe_manager_crud.get_link(
        session=session,
        cafe_id=cafe_id,
        user_id=user_id,
    )
    if link is None:
        raise NotFoundError(
            f'Менеджер {user_id} не привязан к кафе {cafe_id}.',
        )
    await _deactivate_link(session, link)


async def delete_cafe_managers(
    session: AsyncSession,
    actor_role: str,
    cafe_id: int,
) -> None:
    """Отвязывает всех менеджеров от кафе без удаления строк."""
    ensure_admin(actor_role)
    await _ensure_cafe_exists(session, cafe_id)

    links = await cafe_manager_crud.get_managers_by_cafe(
        session=session,
        cafe_id=cafe_id,
    )
    for link in links:
        await _deactivate_link(session, link)
