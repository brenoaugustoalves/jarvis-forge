"""Initial durable execution model."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("projects", sa.Column("id", sa.String(), primary_key=True), sa.Column("data", sa.JSON(), nullable=False))
    op.create_table("workflows", sa.Column("id", sa.String(), primary_key=True), sa.Column("version", sa.Integer(), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("runs", sa.Column("id", sa.String(), primary_key=True), sa.Column("project_id", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("artifacts", sa.Column("id", sa.String(), primary_key=True), sa.Column("run_id", sa.String(), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("action", sa.String(), nullable=False), sa.Column("resource_type", sa.String(), nullable=False), sa.Column("resource_id", sa.String()), sa.Column("metadata", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    for table in ("audit_logs", "artifacts", "runs", "workflows", "projects"): op.drop_table(table)
