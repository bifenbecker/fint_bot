"""add datetime card battle

Revision ID: 82f691f3632c
Revises: da5ce261682d
Create Date: 2025-03-09 18:08:39.808255

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "82f691f3632c"
down_revision: Union[str, None] = "da5ce261682d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cardbattle", sa.Column("date_play", sa.DateTime(), nullable=True))
    op.alter_column(
        "player", "card_battle_rating", existing_type=sa.INTEGER(), nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "player", "card_battle_rating", existing_type=sa.INTEGER(), nullable=True
    )
    op.drop_column("cardbattle", "date_play")
