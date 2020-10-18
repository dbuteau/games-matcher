from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    UnicodeText,
    create_engine,
    PrimaryKeyConstraint
)

Base = declarative_base()


class Games(Base):
    """
    List of all games
    """
    __tablename__ = "Games"
    game_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    application_id = Column(Integer, unique=True, nullable=True)


class Users(Base):
    """
    User policy configuration
    """
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True)
    disallow_globally = Column(Boolean, default=False)
    disallow_guilds = Column(UnicodeText, default=None)
    disallow_users = Column(UnicodeText, default=None)


class Servers(Base):
    """
    Guild configuration
    """
    __tablename__ = "Servers"
    server_id = Column(Integer, primary_key=True)
    prefix = Column(String(1), default="$")


class UserGames(Base):
    """
    List of all games owned by user
    """
    __tablename__ = "UserGames"
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    game_id = Column(Integer, ForeignKey('Games.game_id'))
    last_played_at = Column(DateTime)

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'game_id'),
        {},
    )
