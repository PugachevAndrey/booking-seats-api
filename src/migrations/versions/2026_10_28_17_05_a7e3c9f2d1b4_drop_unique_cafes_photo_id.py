"""drop unique constraint on cafes.photo_id

Revision ID: a7e3c9f2d1b4
Revises: 4563e8d99342
Create Date: 2026-10-28 17:05:31.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7e3c9f2d1b4'
down_revision: Union[str, Sequence[str], None] = '4563e8d99342'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # В первой миграции UNIQUE(photo_id) создан без имени, поэтому PostgreSQL
    # автоматически назвал ограничение по шаблону <table>_<column>_key:
    # cafes_photo_id_key. Поле остаётся nullable FK с ON DELETE SET NULL.
    op.drop_constraint('cafes_photo_id_key', 'cafes', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint('cafes_photo_id_key', 'cafes', ['photo_id'])
