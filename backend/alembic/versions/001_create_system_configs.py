"""
创建system_configs表
Revision ID: 001_create_system_configs
Revises: 
Create Date: 2026-05-23 04:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_create_system_configs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级: 创建system_configs表"""
    op.create_table(
        'system_configs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('key', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('category', sa.String(), nullable=False, index=True),
        sa.Column('encrypted_value', sa.Text(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
    )
    
    # 创建索引
    op.create_index('ix_system_configs_key', 'system_configs', ['key'])
    op.create_index('ix_system_configs_category', 'system_configs', ['category'])


def downgrade():
    """降级: 删除system_configs表"""
    op.drop_index('ix_system_configs_category', table_name='system_configs')
    op.drop_index('ix_system_configs_key', table_name='system_configs')
    op.drop_table('system_configs')
