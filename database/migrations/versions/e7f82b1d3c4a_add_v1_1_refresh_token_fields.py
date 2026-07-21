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
    # Use batch_alter_table for SQLite compatibility when modifying constraints/columns
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "rotation_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(sa.Column("proof_key_thumbprint", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_refresh_tokens_session_id", ["session_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_refresh_tokens_session_id",
            "sessions",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_constraint("fk_refresh_tokens_session_id", type_="foreignkey")
        batch_op.drop_index("ix_refresh_tokens_session_id")
        batch_op.drop_column("proof_key_thumbprint")
        batch_op.drop_column("rotation_count")
        batch_op.drop_column("session_id")
