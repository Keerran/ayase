"""empty message

Revision ID: a47aedb87673
Revises:
Create Date: 2024-07-05 16:21:38.517047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a47aedb87673'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("editions_pkey", "editions")
    op.add_column('editions', sa.Column('edition_id', sa.Integer(), primary_key=True))
    op.create_unique_constraint(op.f('uq_editions_character_id'), 'editions', ['character_id', 'num'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_editions_character_id'), 'editions', type_='unique')
    op.create_primary_key(table_name="editions", columns=["character_id", "num"])
    op.drop_column('editions', 'edition_id')
    # ### end Alembic commands ###
