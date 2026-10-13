from .errors import PermissionDeniedError

ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_USER = 'user'
ROLES = (ROLE_ADMIN, ROLE_MANAGER, ROLE_USER)


def is_admin(role: str) -> bool:
    """Является ли роль администратором."""
    return role == ROLE_ADMIN


def is_manager(role: str) -> bool:
    """Является ли роль менеджером."""
    return role == ROLE_MANAGER


def is_staff(role: str) -> bool:
    """Является ли роль администратором или менеджером."""
    return role in (ROLE_ADMIN, ROLE_MANAGER)


def ensure_staff(role: str) -> None:
    """Требует роль администратора или менеджера."""
    if not is_staff(role):
        raise PermissionDeniedError(
            'Требуется роль администратора или менеджера.',
        )


def ensure_admin(role: str) -> None:
    """Требует роль администратора."""
    if not is_admin(role):
        raise PermissionDeniedError('Требуется роль администратора.')


def ensure_cafe_access(
    role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
) -> None:
    """Админ — любое кафе, менеджер — только своё."""
    if is_admin(role):
        return
    if is_manager(role) and actor_cafe_id == cafe_id:
        return
    raise PermissionDeniedError('Нет прав на управление этим кафе.')


def ensure_owner_or_staff(
    owner_id: int,
    actor_id: int,
    role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
) -> None:
    """Владелец записи, менеджер своего кафе или админ."""
    if is_admin(role):
        return
    if owner_id == actor_id:
        return
    if is_manager(role) and actor_cafe_id == cafe_id:
        return
    raise PermissionDeniedError('Недостаточно прав.')
