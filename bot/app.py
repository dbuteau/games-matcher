# coding: utf-8

"""
This Bot found game in common between 2 member
"""
import os
import sys
import datetime
import logging
from sqlalchemy import (
    or_
)
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from discord import (
    Intents,
    Activity,
    ActivityType,
    channel,
)
from discord.ext import (commands)
from libs.models import (
    engine,
    Games,
    Users,
    UserGames
)
from cogs import (
    owner,
    pubcommands,
    importlibs,
    privacy
)

""" init all external needs """
Session = sessionmaker(bind=engine)
db = Session()
default_level = os.environ.get('BOT_LOG') or logging.ERROR

fo = open("version", "r")
version = fo.readline()

logger = logging.getLogger('discord')
logger.propagate = False
logger.setLevel(int(default_level))
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(f'%(asctime)s [v{version}][%(name)s] - %(levelname)s - %(message)s')
)
logger.addHandler(handler)

intents = Intents.default()
intents.presences = True
intents.members = True
intents.typing = False
intents.messages = True
intents.reactions = True


global prefix


def define_prefix(bot=None, message=None):
    prefix = os.environ.get('BOT_PREFIX') or '$'
    return prefix


bot = commands.Bot(
    command_prefix=define_prefix,
    case_insensitive=True,
    intents=intents,
)


async def default_presence():
    try:
        if define_prefix() != '$test':
            await bot.change_presence(
                activity=Activity(
                    type=ActivityType.watching,
                    name=f"{define_prefix()}help"))
        else:
            await bot.change_presence(
                activity=Activity(
                    type=ActivityType.watching,
                    name="$help"))
    except Exception as err:
        exc_tb = sys.exc_info()[2]
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')


@bot.event
async def on_command_error(ctx, error):
    """ command error listener
        change messages depending of error type
    """
    try:
        owner = (await bot.application_info()).owner
        logger.info(type(error))
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.author.send(
                'Bot is busy! Please retry in a minute',
                delete_after=30)
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.channel.send(
                'This command must be sent to bot by private message only',
                delete_after=30)
            await ctx.message.delete()
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send(
                'This command must be sent on guild server channel only',
                delete_after=30)
        elif (isinstance(error, commands.NotOwner) or
              isinstance(error, commands.MissingPermissions)):
            await ctx.message.delete()
            await ctx.author.send(
                'You are not authorized to use this commands',
                delete_after=30)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send(
                "This command require argument(s), you forgot to give, see \
                `$help <command>` to see what argument it needs",
                delete_after=30)
            await ctx.message.delete()
        elif isinstance(error, UserWarning):
            await ctx.author.send(error)
        elif isinstance(error, commands.BotMissingPermissions):
            msg = f'The bot is missing permission "{error.missing_perms}" to fullfill \
                  "{ctx.message.content}" on {ctx.guild.name}'
            await ctx.guild.owner.send(msg)
            logger.error(msg)
        elif isinstance(error, commands.errors.CommandInvokeError):
            await ctx.author.send(f'{error}')
        else:
            await ctx.author.send("Sorry but i've encountered an error.\
                My Owner was warned, he will investigate and fix me. \
                Please be patient.")
            await owner.send(
                f'{ctx.author.id}>"{ctx.message.content}" encountered error\
                at {datetime.datetime.now()}')
        if not isinstance(ctx.channel, channel.DMChannel):
            if ctx.message:
                await ctx.message.delete()
        logger.error(error)
        await default_presence()
    except Exception as err:
        exc_tb = sys.exc_info()[2]
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')


@bot.event
async def on_command_completion(ctx):
    await default_presence()


@bot.event
async def on_ready():
    """ create server config if not already exist """
    try:
        await default_presence()
        my_guilds = bot.guilds
        for guild in my_guilds:
            me_onguild = guild.me
            logger.info(
                f'{me_onguild} listening "{define_prefix()}" on {guild.name}')
        logger.info(f"Log Level is set to { logging.getLogger('discord') }")
    except Exception as err:
        exc_tb = sys.exc_info()[2]
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')


@bot.event
async def on_member_update(before, after):
    """ listening when user is playing game """
    try:
        if not after.bot and after.activity:
            activity = after.activity
            logger.debug(
                f'detected {activity.name} activity for'
                f'{after.display_name}@{after.id} on {after.guild}')
            if after.activity.type == ActivityType.playing:
                if hasattr(activity, 'application_id'):
                    query = db.query(Games).filter(
                        or_(Games.name == activity.name.lower(),
                            Games.discord_id == activity.application_id))
                else:
                    query = db.query(Games).filter(
                            Games.name == activity.name.lower())
                if query.count() == 0:
                    # add the game to database
                    if hasattr(activity, 'application_id'):
                        oGames = Games(
                            name=activity.name.lower(),
                            discord_id=activity.application_id)
                    else:
                        oGames = Games(name=activity.name.lower())
                    db.add(oGames)
                    db.commit()
                    db.refresh(oGames)
                elif query.count() > 1:
                    raise RuntimeError('Duplicate game')
                else:
                    oGames = query.one()
                    if hasattr(activity, 'application_id'):
                        oGames.discord_id = activity.application_id
                        db.commit()
                        db.refresh(oGames)

                """ we don't save the fact than this user own the game if he
                    didn't allow bot to do it """
                query = db.query(Users).filter(Users.user_id == after.id)
                if query.count() > 0:
                    oUser = query.one()
                else:
                    oUser = Users(user_id=after.id)
                    db.add(oUser)
                    db.commit()
                    db.refresh(oUser)

                if not oUser.disallow_globally:
                    query = db.query(UserGames).filter(
                        UserGames.game_id == oGames.game_id,
                        UserGames.user_id == after.id)
                    if query.count() == 0:
                        db.add(UserGames(
                            game_id=oGames.game_id,
                            user_id=after.id))
                        db.commit()
                        logger.debug("@{} added {}".format(
                                after.id,
                                activity.name.lower()))
                    else:
                        logger.debug(
                            f"@{after.id} already tied "
                            f"to {activity.name.lower()}")
                        """else: bugged
                        oGamesOwned = query.one()
                        oGamesOwned.last_played_at = datetime.datetime.utcnow()
                        db.commit()"""
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')


def run_migrations() -> None:
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, 'head')
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')


if __name__ == '__main__':
    try:
        run_migrations()
        logger.info("Migration ended")

        """ loading Cogs """
        bot.add_cog(pubcommands.Commands(bot, db))
        bot.add_cog(pubcommands.Both(bot, db))
        bot.add_cog(importlibs.Import(bot, db))
        bot.add_cog(privacy.Privacy(bot, db))
        bot.add_cog(owner.SuperAdmin(bot, db))

        bot.help_command.cog = bot.cogs["Misc."]

        bot.run(os.environ['DISCORD_TOKEN'], bot=True, reconnect=True)
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')
