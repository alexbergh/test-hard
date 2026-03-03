"""Initial schema - all tables.

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # --- clusters ---
    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cluster_type", sa.String(50), nullable=False, server_default="kubernetes"),
        sa.Column("k8s_api_url", sa.String(500), nullable=True),
        sa.Column("k8s_token", sa.Text(), nullable=True),
        sa.Column("k8s_ca_cert", sa.Text(), nullable=True),
        sa.Column("k8s_client_cert", sa.Text(), nullable=True),
        sa.Column("k8s_client_key", sa.Text(), nullable=True),
        sa.Column("kubeconfig_path", sa.String(500), nullable=True),
        sa.Column("kubeconfig_context", sa.String(255), nullable=True),
        sa.Column("k8s_namespace", sa.String(255), nullable=True),
        sa.Column("podman_host", sa.String(500), nullable=True),
        sa.Column("podman_tls_verify", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("podman_cert_path", sa.String(500), nullable=True),
        sa.Column("containerd_socket", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("auto_discover", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("discover_filter", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("cluster_version", sa.String(100), nullable=True),
        sa.Column("node_count", sa.Integer(), nullable=True),
        sa.Column("pod_count", sa.Integer(), nullable=True),
        sa.Column("namespace_count", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_clusters_name", "clusters", ["name"])

    # --- hosts ---
    op.create_table(
        "hosts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("host_type", sa.String(50), nullable=False, server_default="container"),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("ssh_user", sa.String(100), nullable=True),
        sa.Column("ssh_key_path", sa.String(500), nullable=True),
        sa.Column("os_family", sa.String(50), nullable=True),
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("architecture", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("enabled_scanners", sa.JSON(), nullable=False),
        sa.Column("scan_profile", sa.String(100), nullable=True),
        sa.Column("last_scan_id", sa.Integer(), nullable=True),
        sa.Column("last_scan_score", sa.Integer(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("k8s_namespace", sa.String(255), nullable=True),
        sa.Column("k8s_pod_name", sa.String(255), nullable=True),
        sa.Column("k8s_node_name", sa.String(255), nullable=True),
        sa.Column("k8s_labels", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("k8s_annotations", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("container_id", sa.String(100), nullable=True),
        sa.Column("container_image", sa.String(500), nullable=True),
        sa.Column("container_runtime", sa.String(50), nullable=True),
        sa.Column("security_context", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_hosts_name", "hosts", ["name"])

    # --- scan_schedules ---
    op.create_table(
        "scan_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scanner", sa.String(50), nullable=False),
        sa.Column("profile", sa.String(100), nullable=True),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("notify_on_completion", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_on_failure", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notification_channels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_scan_schedules_host_id", "scan_schedules", ["host_id"])

    # --- scans ---
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("schedule_id", sa.Integer(), nullable=True),
        sa.Column("scanner", sa.String(50), nullable=False),
        sa.Column("profile", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("warnings", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("errors", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("report_path", sa.String(500), nullable=True),
        sa.Column("html_report_path", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["schedule_id"], ["scan_schedules.id"]),
    )
    op.create_index("ix_scans_host_id", "scans", ["host_id"])

    # --- scan_results ---
    op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("references", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_scan_results_scan_id", "scan_results", ["scan_id"])
    op.create_index("ix_scan_results_rule_id", "scan_results", ["rule_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(50), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("scan_results")
    op.drop_table("scans")
    op.drop_table("scan_schedules")
    op.drop_table("hosts")
    op.drop_table("clusters")
    op.drop_table("users")
