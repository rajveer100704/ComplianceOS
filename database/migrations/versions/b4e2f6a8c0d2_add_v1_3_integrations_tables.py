"""Add v1.3 integrations tables

Revision ID: b4e2f6a8c0d2
Revises: a3f1c2d4e5b6
Create Date: 2026-07-22 15:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "b4e2f6a8c0d2"
down_revision = "a3f1c2d4e5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Create integrations table
    if "integrations" not in tables:
        op.create_table(
            "integrations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "organization_id",
                sa.String(36),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("encrypted_secret", sa.Text(), nullable=True),
            sa.Column("encrypted_access_token", sa.Text(), nullable=True),
            sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
            sa.Column(
                "credential_version",
                sa.Integer(),
                nullable=False,
                server_default="1",
            ),
            sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rotated_by", sa.String(36), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default="1",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.UniqueConstraint(
                "organization_id",
                "provider",
                "name",
                name="uq_integrations_org_provider_name",
            ),
        )
        op.create_index(
            "ix_integrations_org_id",
            "integrations",
            ["organization_id"],
            unique=False,
        )
        op.create_index(
            "ix_integrations_provider",
            "integrations",
            ["provider"],
            unique=False,
        )
        op.create_index(
            "ix_integrations_is_active",
            "integrations",
            ["is_active"],
            unique=False,
        )

    # 2. Create integration_runtime_states table
    if "integration_runtime_states" not in tables:
        op.create_table(
            "integration_runtime_states",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "integration_id",
                sa.String(36),
                sa.ForeignKey("integrations.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "health_status",
                sa.String(50),
                nullable=False,
                server_default="healthy",
            ),
            sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "consecutive_failures",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column("last_error_message", sa.Text(), nullable=True),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_probe_duration_ms", sa.Integer(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.create_index(
            "ix_integration_runtime_states_integration_id",
            "integration_runtime_states",
            ["integration_id"],
            unique=True,
        )
        op.create_index(
            "ix_integration_runtime_states_health_status",
            "integration_runtime_states",
            ["health_status"],
            unique=False,
        )

    # 3. Create integration_delivery_logs table
    if "integration_delivery_logs" not in tables:
        op.create_table(
            "integration_delivery_logs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "integration_id",
                sa.String(36),
                sa.ForeignKey("integrations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "organization_id",
                sa.String(36),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
            sa.Column(
                "status",
                sa.String(50),
                nullable=False,
                server_default="pending",
            ),
            sa.Column(
                "attempt_count",
                sa.Integer(),
                nullable=False,
                server_default="1",
            ),
            sa.Column("response_code", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.create_index(
            "ix_integration_delivery_logs_integration_id",
            "integration_delivery_logs",
            ["integration_id"],
            unique=False,
        )
        op.create_index(
            "ix_integration_delivery_logs_org_id",
            "integration_delivery_logs",
            ["organization_id"],
            unique=False,
        )
        op.create_index(
            "ix_integration_delivery_logs_event_type",
            "integration_delivery_logs",
            ["event_type"],
            unique=False,
        )
        op.create_index(
            "ix_integration_delivery_logs_idempotency_key",
            "integration_delivery_logs",
            ["idempotency_key"],
            unique=True,
        )
        op.create_index(
            "ix_integration_delivery_logs_status",
            "integration_delivery_logs",
            ["status"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("integration_delivery_logs")
    op.drop_table("integration_runtime_states")
    op.drop_table("integrations")
