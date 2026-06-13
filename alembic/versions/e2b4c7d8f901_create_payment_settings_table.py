"""create_payment_settings_table

Revision ID: e2b4c7d8f901
Revises: d9a1e4b6c802
Create Date: 2026-06-13 00:00:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b4c7d8f901'
down_revision: Union[str, Sequence[str], None] = 'd9a1e4b6c802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    now = datetime.utcnow()
    payment_settings = op.create_table(
        'payment_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pix_key', sa.String(length=255), nullable=False),
        sa.Column('pix_key_type', sa.String(length=30), nullable=False),
        sa.Column('recipient_name', sa.String(length=100), nullable=False),
        sa.Column('recipient_city', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.bulk_insert(
        payment_settings,
        [
            {
                'pix_key': '+5547999283466',
                'pix_key_type': 'PHONE',
                'recipient_name': 'Jardel Berti',
                'recipient_city': 'RIO NEGRINHO',
                'created_at': now,
                'updated_at': now,
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('payment_settings')
