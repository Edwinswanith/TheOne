"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-02-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenarios_project_id", "scenarios", ["project_id"])

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_from_run_id", sa.String(length=64), nullable=True),
        sa.Column("changed_decision", sa.String(length=64), nullable=True),
        sa.Column("checkpoint_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_agents", sa.JSON(), nullable=False),
        sa.Column("skipped_agents", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_runs_scenario_status_started", "runs", ["scenario_id", "status", "started_at"])

    op.create_table(
        "state_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state_jsonb", sa.JSON(), nullable=False),
        sa.Column("hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_state_snapshots_scenario_version", "state_snapshots", ["scenario_id", "version"])

    op.create_table(
        "nodes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_id", "node_id", name="uq_nodes_scenario_node_id"),
    )

    op.create_table(
        "edges",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_url"),
    )
    op.create_index("ix_evidence_sources_normalized_url", "evidence_sources", ["normalized_url"])

    op.create_table(
        "node_evidence_map",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_source_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"]),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("decision_key", sa.String(length=64), nullable=False),
        sa.Column("selected_option_id", sa.String(length=64), nullable=False),
        sa.Column("override_justification", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "agent_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("agent", sa.String(length=128), nullable=False),
        sa.Column("inputs_hash", sa.String(length=128), nullable=False),
        sa.Column("outputs_hash", sa.String(length=128), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "exports",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exports_scenario_id", "exports", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("ix_exports_scenario_id", table_name="exports")
    op.drop_table("exports")

    op.drop_table("agent_logs")
    op.drop_table("decisions")
    op.drop_table("node_evidence_map")

    op.drop_index("ix_evidence_sources_normalized_url", table_name="evidence_sources")
    op.drop_table("evidence_sources")

    op.drop_table("edges")
    op.drop_table("nodes")

    op.drop_index("ix_state_snapshots_scenario_version", table_name="state_snapshots")
    op.drop_table("state_snapshots")

    op.drop_index("ix_runs_scenario_status_started", table_name="runs")
    op.drop_table("runs")

    op.drop_index("ix_scenarios_project_id", table_name="scenarios")
    op.drop_table("scenarios")

    op.drop_table("projects")
    op.drop_table("users")
