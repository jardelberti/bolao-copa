"""create_deposit_requests_table

Revision ID: d9a1e4b6c802
Revises: c4f8a2d9e731
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9a1e4b6c802'
down_revision: Union[str, Sequence[str], None] = 'c4f8a2d9e731'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'deposit_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('requested_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('credited_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('proof_image', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('deposit_requests')
