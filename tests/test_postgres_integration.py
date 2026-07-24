"""PostgreSQL-only migration, constraint, cascade, and immutability tests."""

import os
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
DATABASE_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")


@pytest.fixture(scope="module")
def postgres_engine():
    if not DATABASE_URL:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    environment = os.environ.copy()
    environment["APP_DATABASE_URL"] = DATABASE_URL
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"], check=True, env=environment
    )
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=environment
    )
    engine = create_engine(DATABASE_URL)
    try:
        yield engine
    finally:
        engine.dispose()
        subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "base"],
            check=True,
            env=environment,
        )


def test_constraints_cascade_and_audit_immutability(postgres_engine) -> None:
    agent_id = uuid.uuid4()
    policy_id = uuid.uuid4()
    permission_id = uuid.uuid4()
    audit_id = uuid.uuid4()
    user_id = uuid.uuid4()
    with postgres_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO agents
                    (id, name, description, agent_type, status, created_at, updated_at)
                VALUES (:id, 'pg-agent', '', 'test', 'ENABLED', now(), now())
                """
            ),
            {"id": agent_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO policies
                    (id, name, effect, resource, action, conditions, priority, enabled,
                     created_at, updated_at)
                VALUES (:id, 'pg-policy', 'ALLOW', '*', '*', '{}', 1, true, now(), now())
                """
            ),
            {"id": policy_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO permissions (id, agent_id, policy_id, created_at)
                VALUES (:id, :agent_id, :policy_id, now())
                """
            ),
            {"id": permission_id, "agent_id": agent_id, "policy_id": policy_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO audit_logs
                    (id, timestamp, user_id, user_reference, username, agent_id,
                     agent_reference, action, resource, result, policy_id, policy_reference)
                VALUES
                    (:id, now(), :user_id, :user_id, 'pg-user', :agent_id, :agent_id,
                     'agent.create', 'agents', 'success', :policy_id, :policy_id)
                """
            ),
            {
                "id": audit_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "policy_id": policy_id,
            },
        )

    with pytest.raises(DBAPIError), postgres_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO permissions (id, agent_id, policy_id, created_at)
                VALUES (:id, :agent_id, :policy_id, now())
                """
            ),
            {"id": uuid.uuid4(), "agent_id": agent_id, "policy_id": policy_id},
        )

    with postgres_engine.begin() as connection:
        connection.execute(text("DELETE FROM agents WHERE id = :id"), {"id": agent_id})
        assert (
            connection.scalar(
                text("SELECT count(*) FROM permissions WHERE agent_id = :id"),
                {"id": agent_id},
            )
            == 0
        )
        assert (
            connection.scalar(
                text("SELECT agent_reference FROM audit_logs WHERE id = :id"),
                {"id": audit_id},
            )
            == agent_id
        )

    with pytest.raises(DBAPIError), postgres_engine.begin() as connection:
        connection.execute(
            text("UPDATE audit_logs SET result = 'tampered' WHERE id = :id"),
            {"id": audit_id},
        )

    with pytest.raises(DBAPIError), postgres_engine.begin() as connection:
        connection.execute(text("DELETE FROM audit_logs WHERE id = :id"), {"id": audit_id})
