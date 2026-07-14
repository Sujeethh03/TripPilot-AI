"""add trip origin + transport_mode

Revision ID: a1b2c3d4e5f6
Revises: 2c785436e889
Create Date: 2026-07-14 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '2c785436e889'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('trips', sa.Column('origin', sa.String(length=255), nullable=True))
    op.add_column('trips', sa.Column('transport_mode', sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column('trips', 'transport_mode')
    op.drop_column('trips', 'origin')
