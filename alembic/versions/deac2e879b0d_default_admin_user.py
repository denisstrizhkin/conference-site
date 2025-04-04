"""default admin user

Revision ID: deac2e879b0d
Revises: ef00b4f232c1
Create Date: 2025-04-04 11:47:21.669180

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "deac2e879b0d"
down_revision: Union[str, None] = "ef00b4f232c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
insert into user (email, password, role)
values ('admin@example.com', '$2b$12$WWrEeRXZkyC7TKr.arTcCOIwKWZJWo/TnUyxsmqgvbPtbazb67hD6', 'admin');
"""
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("delete from user where email = 'admin@example.com'")
    pass
