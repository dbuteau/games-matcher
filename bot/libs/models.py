from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    DateTime,
    UnicodeText,
    create_engine,
    PrimaryKeyConstraint,
    or_
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import MetaData

engine = create_engine('sqlite:///data/games-matcher-bot.db')
Base = declarative_base()

class Games(Base):
    """
    List of all games
    """
    __tablename__= 'Games'
    game_id      = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name         = Column(String(100), unique=True, nullable=False)
    release_date = Column(Date, nullable=True) # added in v0.0.3
    igdb_id      = Column(Integer, unique=True, nullable=True)
    steam_id     = Column(Integer, unique=True, nullable=True)
    discord_id   = Column(Integer, unique=True, nullable=True)
    multiplayer  = Column(Boolean, nullable=True)
    is_game      = Column(Boolean, default=True) # added in v0.0.10

    def __repr__(self):
        return str(self.__dict__)


class Users(Base):
    """
    User policy configuration
    """
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True)
    disallow_globally = Column(Boolean, default=False)
    disallow_users = Column(UnicodeText, default=None)

class Servers(Base):
    """
    Guild configuration
    """
    __tablename__ = "Servers"
    server_id = Column(Integer, primary_key=True)
    prefix = Column(String(1), default="$")
    banned = Column(Boolean, default=False) # added in v0.0.10

class UserGames(Base):
    """
    List of all games owned by user
    """
    __tablename__ = "UserGames"
    user_id = Column(Integer, ForeignKey('Users.user_id'), autoincrement=False, index=True, primary_key=True)
    game_id = Column(Integer, ForeignKey('Games.game_id'), autoincrement=False, index=True, primary_key=True)
    last_played_at = Column(DateTime, nullable=True)

class WhosUp(Base):
    """
    People Up for a game
    """
    __tablename__ = "WhosUp"
    user_id = Column(Integer, ForeignKey('Users.user_id'), primary_key=True)
    expire_at = Column(DateTime)
