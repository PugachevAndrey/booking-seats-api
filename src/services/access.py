from shared.core.enums import UserRole
from shared.core.errors import PermissionDeniedError

ROLE_ADMIN = UserRole.ADMIN.value
ROLE_MANAGER = UserRole.MANAGER.value
ROLE_USER = UserRole.USER.value
ROLES = tuple(role.value for role in UserRole)


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
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
) -> None:
    """Проверяет доступ к кафе: админ — любое, менеджер — своё."""
    if is_admin(actor_role):
        return
    if is_manager(actor_role) and actor_cafe_id == cafe_id:
        return
    raise PermissionDeniedError('Нет прав на управление этим кафе.')


def ensure_owner_or_staff(
    owner_id: int,
    actor_id: int,
    actor_role: str,
    actor_cafe_id: int | None,
    cafe_id: int,
) -> None:
    """Требует владельца, менеджера кафе или админа."""
    if owner_id == actor_id:
        return
    if is_admin(actor_role):
        return
    if is_manager(actor_role) and actor_cafe_id == cafe_id:
        return
    raise PermissionDeniedError(
        'Нет прав на изменение этой записи.',
    )
