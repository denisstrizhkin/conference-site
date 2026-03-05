"""default admin user

Revision ID: deac2e879b0d
Revises: ef00b4f232c1
Create Date: 2025-04-04 11:47:21.669180

"""

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# Default hash is for local dev only – CI injects ADMIN_PASSWORD_HASH.
_DEFAULT_HASH = "$2b$12$WWrEeRXZkyC7TKr.arTcCOIwKWZJWo/TnUyxsmqgvbPtbazb67hD6"


# revision identifiers, used by Alembic.
revision: str = "deac2e879b0d"
down_revision: Union[str, None] = "ef00b4f232c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", _DEFAULT_HASH)
    op.execute(
        f"""
insert into user (email, password, role)
values ('admin', '{password_hash}', 'admin');
"""
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("delete from user where email = 'admin@example.com'")
    pass
