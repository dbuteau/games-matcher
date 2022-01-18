"""baseline

Revision ID: 22583dfbe57d
Revises:
Create Date: 2021-03-02 18:27:48.695163

"""
from alembic import op
from sqlalchemy.engine.reflection import Inspector
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22583dfbe57d'
down_revision = None
branch_labels = None
depends_on = None

conn = op.get_bind()
inspector = Inspector.from_engine(conn)
tables = inspector.get_table_names()

def upgrade():
    if 'Games' not in tables:
      op.create_table(
        'Games',
        sa.Column('game_id',    sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column('name',       sa.String(100), unique=True, nullable=False),
        sa.Column('igdb_id',    sa.Integer, unique=True, nullable=True),
        sa.Column('steam_id',   sa.Integer, unique=True, nullable=True),
        sa.Column('discord_id', sa.Integer, unique=True, nullable=True),
        sa.Column('multiplayer',sa.Boolean, nullable=True)
      )

    if 'Users' not in tables:
      op.create_table(
        'Users',
        sa.Column('user_id',          sa.Integer, primary_key=True),
        sa.Column('disallow_globally',sa.Boolean, default=False),
        sa.Column('disallow_users',   sa.UnicodeText, default=None)
      )

    if 'Servers' not in tables:
      op.create_table(
        'Servers',
        sa.Column('server_id', sa.Integer, primary_key=True),
        sa.Column('prefix',    sa.String(1), default="$")
      )

    if 'UserGames' not in tables:
      op.create_table(
        'UserGames',
        sa.Column('user_id',        sa.Integer, sa.ForeignKey('Users.user_id'), autoincrement=False, index=True, primary_key=True),
        sa.Column('game_id',        sa.Integer, sa.ForeignKey('Games.game_id'), autoincrement=False, index=True, primary_key=True),
        sa.Column('last_played_at', sa.DateTime, nullable=True)
      )

    if 'WhosUp' not in tables:
      op.create_table(
        'WhosUp',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('Users.user_id'), primary_key=True),
        sa.Column('expire_at', sa.DateTime)
      )

def downgrade():
    op.drop_table('Games')
    op.drop_table('Users')
    op.drop_table('Servers')
    op.drop_table('UserGames')
    op.drop_table('WhosUp')
