"""Add v1.2 multi-tenant tables and migrate user roles to memberships

Revision ID: a3f1c2d4e5b6
Revises: e7f82b1d3c4a
Create Date: 2026-07-22 10:00:00.000000

Changes:
    UP:
      1. Create organizations table
      2. Create organization_memberships table
      3. Create teams table
      4. Create invitations table
      5. Data migration: create personal organization + owner membership for each user
      6. Drop users.role column
      7. Drop users.organization_id column
    DOWN:
      1. Recreate users.role and users.organization_id columns
      2. Drop invitations, teams, organization_memberships, organizations tables
"""

from typing import Sequence, Union
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers
revision: str = "a3f1c2d4e5b6"
down_revision: Union[str, None] = "e7f82b1d3c4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # ──────────────────────────────────────────────────────────────
    # 1. organizations
    # ──────────────────────────────────────────────────────────────
    if "organizations" not in existing_tables:
        op.create_table(
            "organizations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("slug", sa.String(255), nullable=False),
            sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            # AuditMixin columns
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # ──────────────────────────────────────────────────────────────
    # 2. organization_memberships
    # ──────────────────────────────────────────────────────────────
    if "organization_memberships" not in existing_tables:
        op.create_table(
            "organization_memberships",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "organization_id",
                sa.String(36),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(50), nullable=False, server_default="reviewer"),
            sa.Column(
                "invited_by",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
            # AuditMixin columns
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint(
                "organization_id", "user_id", name="uq_org_memberships_org_user"
            ),
        )
        op.create_index(
            "ix_organization_memberships_organization_id",
            "organization_memberships",
            ["organization_id"],
        )
        op.create_index(
            "ix_organization_memberships_user_id",
            "organization_memberships",
            ["user_id"],
        )

    # ──────────────────────────────────────────────────────────────
    # 3. teams
    # ──────────────────────────────────────────────────────────────
    if "teams" not in existing_tables:
        op.create_table(
            "teams",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "organization_id",
                sa.String(36),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("slug", sa.String(255), nullable=False),
            sa.Column("description", sa.String(1000), nullable=True),
            sa.Column(
                "created_by",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            # AuditMixin columns
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_audit", sa.String(36), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_teams_organization_id", "teams", ["organization_id"])
        op.create_index("ix_teams_slug", "teams", ["slug"])

    # ──────────────────────────────────────────────────────────────
    # 4. invitations
    # ──────────────────────────────────────────────────────────────
    if "invitations" not in existing_tables:
        op.create_table(
            "invitations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "organization_id",
                sa.String(36),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("role", sa.String(50), nullable=False, server_default="reviewer"),
            sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column(
                "invited_by",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            # AuditMixin columns
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_invitations_organization_id", "invitations", ["organization_id"])
        op.create_index("ix_invitations_email", "invitations", ["email"])
        op.create_index("ix_invitations_status", "invitations", ["status"])

    # ──────────────────────────────────────────────────────────────
    # 5. Data migration: personal org + owner membership per user
    # ──────────────────────────────────────────────────────────────
    connection = op.get_bind()
    now = _now()

    # Map old UserRole values → MembershipRole values
    role_map = {
        "Owner": "owner",
        "Admin": "admin",
        "Lead Reviewer": "lead_reviewer",
        "Reviewer": "reviewer",
        "Auditor": "auditor",
    }

    users_result = connection.execute(
        sa.text("SELECT id, email, full_name, role FROM users WHERE is_deleted = 0 OR is_deleted = false")
    )
    users = users_result.fetchall()

    for user in users:
        user_id = user[0]
        email = user[1]
        full_name = user[2]
        old_role = user[3] if len(user) > 3 else "Reviewer"

        membership_role = role_map.get(str(old_role), "owner")

        # Create personal organization from email slug
        org_id = _uuid()
        slug_base = email.split("@")[0].lower().replace(".", "-").replace("_", "-")
        slug = f"{slug_base}-org"

        connection.execute(
            sa.text(
                """
                INSERT INTO organizations
                    (id, name, slug, plan, is_active,
                     created_at, updated_at, is_deleted)
                VALUES
                    (:id, :name, :slug, 'free', 1,
                     :now, :now, 0)
                """
            ),
            {"id": org_id, "name": f"{full_name}'s Organization", "slug": slug, "now": now},
        )

        # Create owner membership
        membership_id = _uuid()
        connection.execute(
            sa.text(
                """
                INSERT INTO organization_memberships
                    (id, organization_id, user_id, role, joined_at,
                     created_at, updated_at, is_deleted)
                VALUES
                    (:id, :org_id, :user_id, :role, :now,
                     :now, :now, 0)
                """
            ),
            {
                "id": membership_id,
                "org_id": org_id,
                "user_id": user_id,
                "role": membership_role,
                "now": now,
            },
        )

    # ──────────────────────────────────────────────────────────────
    # 6 & 7. Drop role and organization_id columns from users
    # SQLite does not support DROP COLUMN directly; use batch_alter_table
    # First drop associated indexes so batch_alter_table does not try to recreate them
    # ──────────────────────────────────────────────────────────────
    inspector = sa.inspect(connection)
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_role" in existing_indexes:
        op.drop_index("ix_users_role", table_name="users")
    if "ix_users_organization_id" in existing_indexes:
        op.drop_index("ix_users_organization_id", table_name="users")

    # Drop stale temporary table if previous failed batch operation left it
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_users")

    with op.batch_alter_table("users") as batch_op:
        existing_cols = [c["name"] for c in inspector.get_columns("users")]
        if "role" in existing_cols:
            batch_op.drop_column("role")
        if "organization_id" in existing_cols:
            batch_op.drop_column("organization_id")


def downgrade() -> None:
    # Restore users.role and users.organization_id
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(50),
                nullable=False,
                server_default="Reviewer",
            )
        )
        batch_op.add_column(
            sa.Column("organization_id", sa.String(36), nullable=True)
        )

    # Recreate index definitions dropped during upgrade
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_organization_id", "users", ["organization_id"], unique=False)

    # Drop v1.2 tables in reverse dependency order
    op.drop_table("invitations")
    op.drop_table("teams")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
