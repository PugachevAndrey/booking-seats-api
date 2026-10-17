from datetime import datetime, timezone

from fastapi import APIRouter, status

from schemas.action import ActionCreate, ActionInfo, ActionUpdate

router = APIRouter(prefix='/actions', tags=['Акции'])


def fake_action(id: int = 1) -> dict:  # noqa: A002
    """Временная функция для информации об акции для заглушек."""
    return {
        'id': id,
        'description': 'Скидка 20%',
        'photo_id': None,
        'cafes': [],
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }


@router.get('', response_model=list[ActionInfo])
async def get_actions() -> list:
    """Возвращает список акций."""
    return [fake_action(1), fake_action(2)]


@router.post('', response_model=ActionInfo, status_code=status.HTTP_201_CREATED)
async def create_action(data: ActionCreate) -> dict:
    """Создание акции."""
    return fake_action(3)


@router.get('/{action_id}', response_model=ActionInfo)
async def get_action(action_id: int) -> dict:
    """Информация об акции."""
    return fake_action(action_id)


@router.patch('/{action_id}', response_model=ActionInfo)
async def update_action(action_id: int, data: ActionUpdate) -> dict:
    """Обновить информацию об акции."""
    return fake_action(action_id)
