"""add_tasks_table

Revision ID: 0ee98bee8401
Revises: 914e639ca094
Create Date: 2026-07-18 22:26:59.282841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ee98bee8401'
down_revision: Union[str, Sequence[str], None] = '914e639ca094'
branch_labels: Union[str, Sequence[str], None] = None
branch_label: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tasks',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('retries', sa.Integer(), nullable=False),
    sa.Column('max_retries', sa.Integer(), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('result', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tasks'))
    )
    if op.get_context().dialect.name == "postgresql":
        import pgvector.sqlalchemy
        op.alter_column('document_chunks', 'embedding',
                   existing_type=sa.NUMERIC(precision=512),
                   type_=pgvector.sqlalchemy.vector.VECTOR(dim=512),
                   existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_context().dialect.name == "postgresql":
        import pgvector.sqlalchemy
        op.alter_column('document_chunks', 'embedding',
                   existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=512),
                   type_=sa.NUMERIC(precision=512),
                   existing_nullable=True)
    op.drop_table('tasks')
