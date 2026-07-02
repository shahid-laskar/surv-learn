"""Company hierarchy, multi-tenant RBAC, sessions, audit, notifications

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-01

Adds:
  NEW TABLES (17):
    organization, organization_closure,
    customer, customer_site,
    survapp_role, survapp_permission, survapp_role_permission, survapp_user_role,
    survapp_user_camera,
    camera_group, camera_group_mapping, user_group_mapping,
    user_session, device_token,
    audit_log, notification, password_reset_token

  ALTER EXISTING:
    survapp_user         — add email, mobile, first_name, last_name, user_type,
                           organization_id, customer_id, is_locked, failed_login_count,
                           last_password_change, created_by, updated_by, updated_at
    survapp_camera_master — add customer_id, customer_site_id, organization_id,
                            camera_model, manufacturer
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────
    # 1. organization
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "organization",
        sa.Column("id",         sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("parent_id",  sa.BigInteger(), sa.ForeignKey("organization.id"), nullable=True),
        sa.Column("code",       sa.String(50),   nullable=False),
        sa.Column("name",       sa.String(200),  nullable=False),
        sa.Column("type",       sa.String(50),   nullable=False),   # ROOT|CIRCLE|BA|SSA|DISTRICT|SITE|NOC
        sa.Column("is_active",  sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("code", name="uq_org_code"),
    )
    op.create_index("ix_org_id",        "organization", ["id"])
    op.create_index("ix_org_parent_id", "organization", ["parent_id"])

    # ─────────────────────────────────────────────────────────────────
    # 2. organization_closure  (precomputed ancestor/descendant pairs)
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "organization_closure",
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("child_id",  sa.BigInteger(), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("depth",     sa.Integer(),    nullable=False),
        sa.PrimaryKeyConstraint("parent_id", "child_id"),
    )
    op.create_index("ix_org_closure_child", "organization_closure", ["child_id"])

    # ─────────────────────────────────────────────────────────────────
    # 3. customer
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "customer",
        sa.Column("id",                 sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("parent_customer_id", sa.BigInteger(), sa.ForeignKey("customer.id"), nullable=True),
        sa.Column("customer_code",      sa.String(100),  nullable=True),
        sa.Column("name",               sa.String(200),  nullable=False),
        sa.Column("customer_type",      sa.String(50),   nullable=True),  # ENTERPRISE|BANK|SCHOOL|...
        sa.Column("organization_id",    sa.BigInteger(), sa.ForeignKey("organization.id"), nullable=True),
        sa.Column("email",              sa.String(255),  nullable=True),
        sa.Column("phone",              sa.String(30),   nullable=True),
        sa.Column("address",            sa.Text(),       nullable=True),
        sa.Column("is_active",          sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at",         sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at",         sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("customer_code", name="uq_customer_code"),
    )
    op.create_index("ix_customer_id",   "customer", ["id"])
    op.create_index("ix_customer_org",  "customer", ["organization_id"])

    # ─────────────────────────────────────────────────────────────────
    # 4. customer_site
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "customer_site",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.BigInteger(), sa.ForeignKey("customer.id"), nullable=False),
        sa.Column("site_code",   sa.String(100),  nullable=True),
        sa.Column("name",        sa.String(200),  nullable=True),
        sa.Column("state",       sa.String(100),  nullable=True),
        sa.Column("district",    sa.String(100),  nullable=True),
        sa.Column("city",        sa.String(100),  nullable=True),
        sa.Column("address",     sa.Text(),       nullable=True),
        sa.Column("latitude",    sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude",   sa.Numeric(10, 7), nullable=True),
        sa.Column("is_active",   sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_customer_site_id",       "customer_site", ["id"])
    op.create_index("ix_customer_site_customer",  "customer_site", ["customer_id"])

    # ─────────────────────────────────────────────────────────────────
    # 5. survapp_role
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "survapp_role",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code",        sa.String(100),  nullable=False),
        sa.Column("name",        sa.String(100),  nullable=True),
        sa.Column("description", sa.Text(),       nullable=True),
        sa.UniqueConstraint("code", name="uq_role_code"),
    )
    op.create_index("ix_role_id", "survapp_role", ["id"])

    # ─────────────────────────────────────────────────────────────────
    # 6. survapp_permission
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "survapp_permission",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code",        sa.String(100),  nullable=False),
        sa.Column("name",        sa.String(200),  nullable=True),
        sa.Column("description", sa.Text(),       nullable=True),
        sa.UniqueConstraint("code", name="uq_permission_code"),
    )
    op.create_index("ix_permission_id", "survapp_permission", ["id"])

    # ─────────────────────────────────────────────────────────────────
    # 7. survapp_role_permission
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "survapp_role_permission",
        sa.Column("role_id",       sa.BigInteger(), sa.ForeignKey("survapp_role.id"), nullable=False),
        sa.Column("permission_id", sa.BigInteger(), sa.ForeignKey("survapp_permission.id"), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # ─────────────────────────────────────────────────────────────────
    # 8. survapp_user_role
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "survapp_user_role",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("survapp_user.id"), nullable=False),
        sa.Column("role_id", sa.BigInteger(), sa.ForeignKey("survapp_role.id"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # ─────────────────────────────────────────────────────────────────
    # 9. camera_group
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "camera_group",
        sa.Column("id",              sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name",            sa.String(200),  nullable=False),
        sa.Column("organization_id", sa.BigInteger(), sa.ForeignKey("organization.id"), nullable=True),
        sa.Column("customer_id",     sa.BigInteger(), sa.ForeignKey("customer.id"),     nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_camera_group_id", "camera_group", ["id"])

    # ─────────────────────────────────────────────────────────────────
    # 10. camera_group_mapping
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "camera_group_mapping",
        sa.Column("group_id",  sa.BigInteger(), sa.ForeignKey("camera_group.id"), nullable=False),
        sa.Column("camera_id", sa.BigInteger(), sa.ForeignKey("survapp_camera_master.id"), nullable=False),
        sa.PrimaryKeyConstraint("group_id", "camera_id"),
    )

    # ─────────────────────────────────────────────────────────────────
    # 11. user_group_mapping
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "user_group_mapping",
        sa.Column("user_id",  sa.BigInteger(), sa.ForeignKey("survapp_user.id"),   nullable=False),
        sa.Column("group_id", sa.BigInteger(), sa.ForeignKey("camera_group.id"),   nullable=False),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )

    # ─────────────────────────────────────────────────────────────────
    # 12. survapp_user_camera  (direct per-user camera overrides)
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "survapp_user_camera",
        sa.Column("user_id",   sa.BigInteger(), sa.ForeignKey("survapp_user.id"),           nullable=False),
        sa.Column("camera_id", sa.BigInteger(), sa.ForeignKey("survapp_camera_master.id"),  nullable=False),
        sa.PrimaryKeyConstraint("user_id", "camera_id"),
    )

    # ─────────────────────────────────────────────────────────────────
    # 13. user_session
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "user_session",
        sa.Column("id",                 sa.String(36),   primary_key=True),   # UUID stored as VARCHAR
        sa.Column("user_id",            sa.BigInteger(), sa.ForeignKey("survapp_user.id"), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(),       nullable=True),
        sa.Column("device_name",        sa.String(200),  nullable=True),
        sa.Column("device_type",        sa.String(100),  nullable=True),
        sa.Column("ip_address",         sa.String(100),  nullable=True),
        sa.Column("created_at",         sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active",          sa.Boolean(),    nullable=False, server_default="true"),
    )
    op.create_index("ix_user_session_user_id", "user_session", ["user_id"])

    # ─────────────────────────────────────────────────────────────────
    # 14. device_token  (FCM/APNs push tokens)
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "device_token",
        sa.Column("id",         sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id",    sa.BigInteger(), sa.ForeignKey("survapp_user.id"), nullable=False),
        sa.Column("platform",   sa.String(20),   nullable=True),    # android|ios|web
        sa.Column("token",      sa.Text(),       nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_device_token_user_id", "device_token", ["user_id"])

    # ─────────────────────────────────────────────────────────────────
    # 15. audit_log  (immutable — never updated, only inserted)
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id",          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id",     sa.BigInteger(), nullable=True),
        sa.Column("username",    sa.String(100),  nullable=True),
        sa.Column("action",      sa.String(100),  nullable=False),   # CREATE|UPDATE|DELETE|LOGIN|LOGOUT
        sa.Column("entity_type", sa.String(100),  nullable=True),    # camera|user|customer|...
        sa.Column("entity_id",   sa.String(100),  nullable=True),
        sa.Column("old_value",   sa.JSON(),        nullable=True),
        sa.Column("new_value",   sa.JSON(),        nullable=True),
        sa.Column("ip_address",  sa.String(100),  nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_audit_log_id",          "audit_log", ["id"])
    op.create_index("ix_audit_log_user_id",     "audit_log", ["user_id"])
    op.create_index("ix_audit_log_entity",      "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_log_created_at",  "audit_log", ["created_at"])

    # ─────────────────────────────────────────────────────────────────
    # 16. notification
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "notification",
        sa.Column("id",         sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id",    sa.BigInteger(), sa.ForeignKey("survapp_user.id"), nullable=True),
        sa.Column("title",      sa.String(500),  nullable=True),
        sa.Column("message",    sa.Text(),       nullable=True),
        sa.Column("payload",    sa.JSON(),        nullable=True),
        sa.Column("is_read",    sa.Boolean(),    nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_notification_id",      "notification", ["id"])
    op.create_index("ix_notification_user_id", "notification", ["user_id"])

    # ─────────────────────────────────────────────────────────────────
    # 17. password_reset_token
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "password_reset_token",
        sa.Column("id",         sa.String(36),   primary_key=True),  # UUID
        sa.Column("user_id",    sa.BigInteger(), sa.ForeignKey("survapp_user.id"), nullable=False),
        sa.Column("token_hash", sa.Text(),       nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used",       sa.Boolean(),    nullable=False, server_default="false"),
    )
    op.create_index("ix_prt_user_id", "password_reset_token", ["user_id"])

    # ─────────────────────────────────────────────────────────────────
    # ALTER survapp_user — add new columns (preserve existing rows)
    # ─────────────────────────────────────────────────────────────────
    op.add_column("survapp_user", sa.Column("email",                sa.String(255), nullable=True))
    op.add_column("survapp_user", sa.Column("mobile",               sa.String(20),  nullable=True))
    op.add_column("survapp_user", sa.Column("first_name",           sa.String(100), nullable=True))
    op.add_column("survapp_user", sa.Column("last_name",            sa.String(100), nullable=True))
    op.add_column("survapp_user", sa.Column("user_type",            sa.String(30),  nullable=False,
                                            server_default="EMPLOYEE"))
    op.add_column("survapp_user", sa.Column("organization_id",      sa.BigInteger(),
                                            sa.ForeignKey("organization.id"), nullable=True))
    op.add_column("survapp_user", sa.Column("customer_id",          sa.BigInteger(),
                                            sa.ForeignKey("customer.id"), nullable=True))
    op.add_column("survapp_user", sa.Column("is_locked",            sa.Boolean(),   nullable=False,
                                            server_default="false"))
    op.add_column("survapp_user", sa.Column("failed_login_count",   sa.Integer(),   nullable=False,
                                            server_default="0"))
    op.add_column("survapp_user", sa.Column("last_password_change", sa.DateTime(timezone=True), nullable=True))
    op.add_column("survapp_user", sa.Column("created_by",           sa.BigInteger(), nullable=True))
    op.add_column("survapp_user", sa.Column("updated_by",           sa.BigInteger(), nullable=True))
    op.add_column("survapp_user", sa.Column("updated_at",           sa.DateTime(timezone=True),
                                            nullable=True, server_default=sa.text("NOW()")))

    # ─────────────────────────────────────────────────────────────────
    # ALTER survapp_camera_master — add org/customer linkage columns
    # ─────────────────────────────────────────────────────────────────
    op.add_column("survapp_camera_master", sa.Column("customer_id",      sa.BigInteger(),
                                                     sa.ForeignKey("customer.id"), nullable=True))
    op.add_column("survapp_camera_master", sa.Column("customer_site_id", sa.BigInteger(),
                                                     sa.ForeignKey("customer_site.id"), nullable=True))
    op.add_column("survapp_camera_master", sa.Column("organization_id",  sa.BigInteger(),
                                                     sa.ForeignKey("organization.id"), nullable=True))
    op.add_column("survapp_camera_master", sa.Column("camera_model",     sa.String(100), nullable=True))
    op.add_column("survapp_camera_master", sa.Column("manufacturer",     sa.String(100), nullable=True))


def downgrade() -> None:
    # Reverse ALTER on existing tables first
    op.drop_column("survapp_camera_master", "manufacturer")
    op.drop_column("survapp_camera_master", "camera_model")
    op.drop_column("survapp_camera_master", "organization_id")
    op.drop_column("survapp_camera_master", "customer_site_id")
    op.drop_column("survapp_camera_master", "customer_id")

    op.drop_column("survapp_user", "updated_at")
    op.drop_column("survapp_user", "updated_by")
    op.drop_column("survapp_user", "created_by")
    op.drop_column("survapp_user", "last_password_change")
    op.drop_column("survapp_user", "failed_login_count")
    op.drop_column("survapp_user", "is_locked")
    op.drop_column("survapp_user", "customer_id")
    op.drop_column("survapp_user", "organization_id")
    op.drop_column("survapp_user", "user_type")
    op.drop_column("survapp_user", "last_name")
    op.drop_column("survapp_user", "first_name")
    op.drop_column("survapp_user", "mobile")
    op.drop_column("survapp_user", "email")

    # Drop new tables in reverse dependency order
    op.drop_table("password_reset_token")
    op.drop_table("notification")
    op.drop_table("audit_log")
    op.drop_table("device_token")
    op.drop_table("user_session")
    op.drop_table("survapp_user_camera")
    op.drop_table("user_group_mapping")
    op.drop_table("camera_group_mapping")
    op.drop_table("camera_group")
    op.drop_table("survapp_user_role")
    op.drop_table("survapp_role_permission")
    op.drop_table("survapp_permission")
    op.drop_table("survapp_role")
    op.drop_table("customer_site")
    op.drop_table("customer")
    op.drop_table("organization_closure")
    op.drop_table("organization")
