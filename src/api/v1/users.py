from datetime import datetime, timezone

from fastapi import APIRouter, status

from schemas.user import UserCreate, UserInfo, UserUpdate

from core.enums import UserRole

router = APIRouter(prefix='/users', tags=['Пользователи'])


def get_fake_user(user_id: int = 1, username: str = 'fakeuser') -> dict:  # noqa: A002
    """Временная функция для информации о пользователе для заглушек."""
    return {
        'id': user_id,
        'username': username,
        'email': f'{username}@mail.ru',
        'phone': '+78005553535',
        'tg_id': '123456',
        'role': UserRole.USER,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[UserInfo])
async def get_all_users() -> list:
    """Получение списка пользователей."""
    return [get_fake_user(1, 'admin'), get_fake_user(2, 'user1')]


@router.post('', response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate) -> dict:
    """Регистрация нового пользователя."""
    fake = get_fake_user(3, data.username)
    fake['email'] = data.email or fake['email']
    fake['phone'] = data.phone or fake['phone']
    return fake


@router.get('/me', response_model=UserInfo)
async def get_me() -> dict:
    """Информация о текущем пользователе."""
    return get_fake_user(1, 'current_user')


@router.patch('/me', response_model=UserInfo)
async def update_me(data: UserUpdate) -> dict:
    """Обновление текущего пользователя."""
    fake = get_fake_user(1, 'current_user')
    if data.username:
        fake['username'] = data.username
    return fake


@router.get('/{user_id}', response_model=UserInfo)
async def get_user_by_id(user_id: int) -> dict:
    """Получение пользователя по ID."""
    return get_fake_user(user_id, f'user_{user_id}')


@router.patch('/{user_id}', response_model=UserInfo)
async def update_user_by_id(user_id: int, data: UserUpdate) -> dict:
    """Обновление пользователя по ID."""
    fake = get_fake_user(user_id, f'user_{user_id}')
    if data.role:
        fake['role'] = data.role
    if data.is_active is not None:
        fake['is_active'] = data.is_active
    return fake
