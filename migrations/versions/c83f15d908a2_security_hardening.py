"""security hardening

Revision ID: c83f15d908a2
Revises: a6f06b9c2d11
"""

import sqlalchemy as sa
from alembic import op

revision = "c83f15d908a2"
down_revision = "a6f06b9c2d11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column(
        "users", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        "users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0")
    )
    op.create_index("ix_users_enabled", "users", ["enabled"], unique=False)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_auth_sessions_refresh_token_hash",
        "auth_sessions",
        ["refresh_token_hash"],
        unique=True,
    )
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False)
    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(100), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "audit_logs",
        sa.Column("decision_context", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column("audit_logs", sa.Column("policy_version", sa.String(100), nullable=True))
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_column("audit_logs", "policy_version")
    op.drop_column("audit_logs", "decision_context")
    op.drop_column("audit_logs", "metadata_json")
    op.drop_column("audit_logs", "correlation_id")
    op.drop_table("auth_sessions")
    op.drop_index("ix_users_enabled", table_name="users")
    op.drop_column("users", "token_version")
    op.drop_column("users", "enabled")
    op.drop_column("users", "password_hash")
