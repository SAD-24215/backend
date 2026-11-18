"""Add roles

Revision ID: 1859e2b05970
Revises: e363c3191c28
Create Date: 2026-11-14 22:58:39.463607

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1859e2b05970"
down_revision: Union[str, Sequence[str], None] = "e363c3191c28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (name)
        VALUES ('admin'), ('marshal'), ('customer')
        ON CONFLICT (name) DO NOTHING
        """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM roles
        WHERE name IN ('admin', 'marshal', 'customer')
        """)
