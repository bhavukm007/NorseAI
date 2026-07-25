"""add financial governance core

Revision ID: a6f06b9c2d11
Revises: f4a07a376d4e
"""

import sqlalchemy as sa
from alembic import op

revision = "a6f06b9c2d11"
down_revision = "f4a07a376d4e"
branch_labels = None
depends_on = None

governance_status = sa.Enum(
    "ENABLED", "DISABLED", "EMERGENCY_STOPPED", name="governancestatus", native_enum=False
)
limit_period = sa.Enum("DAILY", "MONTHLY", "TRANSACTION", name="limitperiod", native_enum=False)
action_type = sa.Enum(
    "PAYMENT", "TRANSFER", "REFUND", name="financialactiontype", native_enum=False
)
action_status = sa.Enum(
    "REJECTED", "SETTLED", "REVERSED", name="financialactionstatus", native_enum=False
)
reservation_status = sa.Enum(
    "RESERVED", "SETTLED", "RELEASED", "REVERSED", name="reservationstatus", native_enum=False
)
record_type = sa.Enum("SETTLEMENT", "REVERSAL", name="spendrecordtype", native_enum=False)


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("status", governance_status, nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)
    op.create_index("ix_organizations_status", "organizations", ["status"])

    op.create_table(
        "fleets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("status", governance_status, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_fleets_organization_id", "fleets", ["organization_id"])
    op.create_index("ix_fleets_name", "fleets", ["name"], unique=True)
    op.create_index("ix_fleets_status", "fleets", ["status"])

    with op.batch_alter_table("agents") as batch:
        batch.add_column(sa.Column("fleet_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_agents_fleet_id", "fleets", ["fleet_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_index("ix_agents_fleet_id", ["fleet_id"])
    with op.batch_alter_table("policies") as batch:
        batch.add_column(
            sa.Column(
                "allows_uncapped_spend",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    op.create_table(
        "fleet_spend_limits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("fleet_id", sa.Uuid(), nullable=False),
        sa.Column("period", limit_period, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fleet_id", "period", "currency"),
    )
    op.create_index("ix_fleet_spend_limits_fleet_id", "fleet_spend_limits", ["fleet_id"])

    op.create_table(
        "organization_spend_limits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("period", limit_period, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "period", "currency"),
    )
    op.create_index(
        "ix_organization_spend_limits_organization_id",
        "organization_spend_limits",
        ["organization_id"],
    )

    op.create_table(
        "financial_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("fleet_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", action_type, nullable=False),
        sa.Column("resource", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", action_status, nullable=False),
        sa.Column("permission_allowed", sa.Boolean(), nullable=False),
        sa.Column("spend_allowed", sa.Boolean(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("adapter_reference", sa.String(150), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fleet_id"], ["fleets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "idempotency_key"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_financial_actions_request_id", "financial_actions", ["request_id"])
    op.create_index("ix_financial_actions_agent_id", "financial_actions", ["agent_id"])
    op.create_index("ix_financial_actions_fleet_id", "financial_actions", ["fleet_id"])
    op.create_index(
        "ix_financial_actions_organization_id", "financial_actions", ["organization_id"]
    )
    op.create_index("ix_financial_actions_status", "financial_actions", ["status"])
    op.create_index("ix_financial_actions_timestamp", "financial_actions", ["timestamp"])
    op.create_index(
        "ix_financial_actions_fleet_timestamp",
        "financial_actions",
        ["fleet_id", "timestamp"],
    )

    op.create_table(
        "budget_reservations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("financial_action_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("fleet_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", reservation_status, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["financial_action_id"], ["financial_actions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("financial_action_id"),
    )
    for column in ("financial_action_id", "agent_id", "fleet_id", "organization_id", "status"):
        op.create_index(f"ix_budget_reservations_{column}", "budget_reservations", [column])

    with op.batch_alter_table("spend_records") as batch:
        batch.add_column(
            sa.Column(
                "record_type",
                record_type,
                nullable=False,
                server_default="SETTLEMENT",
            )
        )
        batch.add_column(sa.Column("financial_action_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_spend_records_financial_action_id",
            "financial_actions",
            ["financial_action_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_spend_records_financial_action_id", ["financial_action_id"])

    with op.batch_alter_table("audit_logs") as batch:
        batch.add_column(sa.Column("request_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("fleet_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("organization_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("amount", sa.Numeric(18, 2), nullable=True))
        batch.add_column(sa.Column("currency", sa.String(3), nullable=True))
        batch.add_column(sa.Column("policy_decision", sa.String(50), nullable=True))
        batch.add_column(sa.Column("spend_decision", sa.String(50), nullable=True))
        batch.add_column(sa.Column("execution_result", sa.String(50), nullable=True))
        batch.create_index("ix_audit_logs_request_id", ["request_id"])
        batch.create_index("ix_audit_logs_fleet_id", ["fleet_id"])
        batch.create_index("ix_audit_logs_organization_id", ["organization_id"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE TRIGGER spend_records_immutable
            BEFORE UPDATE OR DELETE ON spend_records
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
            """
        )
    elif op.get_bind().dialect.name == "sqlite":
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            BEGIN SELECT RAISE(ABORT, 'audit_logs are immutable'); END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            BEGIN SELECT RAISE(ABORT, 'audit_logs are immutable'); END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER spend_records_no_update
            BEFORE UPDATE ON spend_records
            BEGIN SELECT RAISE(ABORT, 'spend_records are immutable'); END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER spend_records_no_delete
            BEFORE DELETE ON spend_records
            BEGIN SELECT RAISE(ABORT, 'spend_records are immutable'); END;
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER spend_records_immutable ON spend_records")
    elif op.get_bind().dialect.name == "sqlite":
        op.execute("DROP TRIGGER spend_records_no_update")
        op.execute("DROP TRIGGER spend_records_no_delete")

    with op.batch_alter_table("audit_logs") as batch:
        for index in (
            "ix_audit_logs_organization_id",
            "ix_audit_logs_fleet_id",
            "ix_audit_logs_request_id",
        ):
            batch.drop_index(index)
        for column in (
            "execution_result",
            "spend_decision",
            "policy_decision",
            "currency",
            "amount",
            "organization_id",
            "fleet_id",
            "request_id",
        ):
            batch.drop_column(column)
    with op.batch_alter_table("spend_records") as batch:
        batch.drop_index("ix_spend_records_financial_action_id")
        batch.drop_constraint("fk_spend_records_financial_action_id", type_="foreignkey")
        batch.drop_column("financial_action_id")
        batch.drop_column("record_type")
    op.drop_table("budget_reservations")
    op.drop_table("financial_actions")
    op.drop_table("organization_spend_limits")
    op.drop_table("fleet_spend_limits")
    with op.batch_alter_table("policies") as batch:
        batch.drop_column("allows_uncapped_spend")
    with op.batch_alter_table("agents") as batch:
        batch.drop_index("ix_agents_fleet_id")
        batch.drop_constraint("fk_agents_fleet_id", type_="foreignkey")
        batch.drop_column("fleet_id")
    op.drop_table("fleets")
    op.drop_table("organizations")
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            BEGIN SELECT RAISE(ABORT, 'audit_logs are immutable'); END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            BEGIN SELECT RAISE(ABORT, 'audit_logs are immutable'); END;
            """
        )
