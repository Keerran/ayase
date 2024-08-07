"""empty message

Revision ID: 9b899bbc5c65
Revises: fa708a3ec141
Create Date: 2024-07-20 19:26:25.266974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b899bbc5c65'
down_revision: Union[str, None] = 'fa708a3ec141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cards', sa.Column('grabbed_by', sa.BigInteger(), nullable=True))
    op.execute("UPDATE cards SET grabbed_by = user_id WHERE grabbed_by is NULL;")
    op.alter_column("cards", "grabbed_by", nullable=False)
    op.create_foreign_key(op.f('fk_cards_grabbed_by_users'), 'cards', 'users', ['grabbed_by'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_cards_grabbed_by_users'), 'cards', type_='foreignkey')
    op.drop_column('cards', 'grabbed_by')
    # ### end Alembic commands ###
