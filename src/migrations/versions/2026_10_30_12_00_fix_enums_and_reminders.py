"""Fix enums, add unique username and booking reminders

Revision ID: fix_2026_10_30
Revises: a7e3c9f2d1b4
Create Date: 2026-10-30 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_2026_10_30'
down_revision: Union[str, Sequence[str], None] = 'a7e3c9f2d1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Безопасно обновляем старые Enum'ы на новые (КАПС)
    op.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'MANAGER' WHERE role = 'manager'")
    op.execute("UPDATE users SET role = 'USER' WHERE role = 'user'")

    op.execute("UPDATE booking SET status = 'BOOKING' WHERE status = 'booking'")
    op.execute("UPDATE booking SET status = 'CANCELED' WHERE status = 'cancelled'")
    op.execute("UPDATE booking SET status = 'COMPLETED' WHERE status = 'completed'")
    op.execute("UPDATE booking SET status = 'ACTIVE' WHERE status = 'active'")

    # 2. Добавляем уникальность на username
    op.create_unique_constraint('uq_users_username', 'users', ['username'])

    # 3. Добавляем поля для напоминаний в таблицу booking
    op.add_column('booking', sa.Column('remind_before_minutes', sa.Integer(), nullable=True, comment='За сколько минут напомнить'))
    op.add_column('booking', sa.Column('reminder_task_id', sa.String(length=155), nullable=True, comment='ID задачи Celery'))


def downgrade() -> None:
    # Откат изменений (на случай, если что-то пойдет не так)
    op.drop_column('booking', 'reminder_task_id')
    op.drop_column('booking', 'remind_before_minutes')
    op.drop_constraint('uq_users_username', 'users', type_='unique')

    op.execute("UPDATE users SET role = 'admin' WHERE role = 'ADMIN'")
    op.execute("UPDATE users SET role = 'manager' WHERE role = 'MANAGER'")
    op.execute("UPDATE users SET role = 'user' WHERE role = 'USER'")

    op.execute("UPDATE booking SET status = 'booking' WHERE status = 'BOOKING'")
    op.execute("UPDATE booking SET status = 'cancelled' WHERE status = 'CANCELED'")
    op.execute("UPDATE booking SET status = 'completed' WHERE status = 'COMPLETED'")
    op.execute("UPDATE booking SET status = 'active' WHERE status = 'ACTIVE'")
