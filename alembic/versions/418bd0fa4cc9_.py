"""empty message

Revision ID: 418bd0fa4cc9
Revises: 15ed16a907c1
Create Date: 2024-07-08 00:42:10.246577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '418bd0fa4cc9'
down_revision: Union[str, None] = '15ed16a907c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cards', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.alter_column('cards', "card_id", new_column_name="id")
    op.execute("ALTER SEQUENCE cards_card_id_seq RENAME TO cards_id_seq;")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cards', 'created_at')
    op.alter_column('cards', "id", new_column_name="card_id")
    op.execute("ALTER SEQUENCE cards_id_seq RENAME TO cards_card_id_seq;")
    # ### end Alembic commands ###