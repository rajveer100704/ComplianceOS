"""Add v1.1 refresh token fields (session_id, rotation_count, proof_key_thumbprint)

Revision ID: e7f82b1d3c4a
Revises: bccc9a1c6b5c
Create Date: 2026-07-21 15:32:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e7f82b1d3c4a"
down_revision: Union[str, None] = "bccc9a1c6b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to refresh_tokens table
    op.add_column(
        "refresh_tokens",
        sa.Column("session_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "rotation_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("proof_key_thumbprint", sa.String(length=255), nullable=True),
    )

    op.create_index(
        op.f("ix_refresh_tokens_session_id"),
        "refresh_tokens",
        ["session_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_refresh_tokens_session_id",
        "refresh_tokens",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_refresh_tokens_session_id", "refresh_tokens", type_="foreignkey")
    op.drop_index(op.f("ix_refresh_tokens_session_id"), table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "proof_key_thumbprint")
    op.drop_column("refresh_tokens", "rotation_count")
    op.drop_column("refresh_tokens", "session_id")
