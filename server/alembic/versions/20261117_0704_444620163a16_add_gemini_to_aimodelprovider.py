"""add gemini to AIModelProvider

Revision ID: 444620163a16
Revises: b7d2e9a4c1f3
Create Date: 2026-11-17 07:04:31.780446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '444620163a16'
down_revision: Union[str, Sequence[str], None] = 'b7d2e9a4c1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    ALTER TYPE ai_model_provider ADD VALUE 'gemini'
    """
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE ai_model_provider ADD VALUE IF NOT EXISTS 'gemini'")


def downgrade() -> None:
    """Downgrade schema.
    PostgreSQL không hỗ trợ xoá giá trị enum.
    'gemini' được giữ lại trong ai_model_provider (vô hại với code cũ nếu không có dữ liệu dùng nó).
    """
    pass
