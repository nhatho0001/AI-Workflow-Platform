"""messages.content VARCHAR(2000) -> TEXT

Câu trả lời của LLM thường dài hơn 2000 ký tự.

Revision ID: b7d2e9a4c1f3
Revises: f4c3ad9ca3c1
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d2e9a4c1f3'
down_revision: Union[str, Sequence[str], None] = 'f4c3ad9ca3c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'messages', 'content',
        existing_type=sa.String(length=2000),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Cắt bớt nội dung dài hơn 2000 ký tự, nếu không ALTER sẽ lỗi
    op.alter_column(
        'messages', 'content',
        existing_type=sa.Text(),
        type_=sa.String(length=2000),
        existing_nullable=False,
        postgresql_using='left(content, 2000)',
    )
