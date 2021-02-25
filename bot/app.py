# coding: utf-8

"""
This Bot found game in common between 2 member
"""
import os
import sys
import datetime
import logging
import json
import discord
import DiscordUtils
import asyncio
from discord.ext import commands
from discord.user import User
from cogs import matcher, gImport, privacy
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from libs.models import Users, Games, UserGames, Servers, Base, WhosUp
from  libs.interntools import interntools
from libs.steam import Steam

fo = open("version", "r")
version = fo.readline()

default_prefix = '$'

logging.basicConfig(stream=sys.stdout, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

engine = create_engine('sqlite:///data/games-matcher-bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.typing = False
intents.guild_messages = True

async def determine_prefix(bot, message):
    query = db.query(Servers).filter(server_id=guild.id)
    if query.count() > 0:
        return query.one().prefix
    else:
        return default_prefix

bot = commands.Bot(command_prefix=default_prefix, intents=intents)
bot.add_cog(matcher.Functions(bot,db))
bot.add_cog(gImport.Import(bot,db))
bot.add_cog(privacy.Privacy(bot,db))


# Init Error messages
MESSAGES = {
    'EXCEPTION': "Oups! I've encountered an unattended error and warned my maker about it",
    'HEY': "{0.user} Unattended error, please check logs at {1}",
    'NO_DATA': "Sorry i don't have data about {0.user}",
    'NOT_IMPLEMENTED': 'Sorry but this command is not yet implemented'
}

async def report_error(ctx, arg, line=0):
    logging.error(line, arg)
    await ctx.author.send(MESSAGES['EXCEPTION'])
    owner = (await bot.application_info()).owner
    await owner.send(MESSAGES['HEY'].format(bot, datetime.datetime.now().strftime('%B %d %Y - %H:%M:%S')))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MaxConcurrencyReached):
        await ctx.author.send('Bot is busy! Please retry in a minute')
    elif isinstance(error, commands.PrivateMessageOnly):
        msg = await ctx.channel.send('This command must be sent to bot by private message only')
        await ctx.message.delete()
        await asyncio.sleep(30)
        msg.delete()
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.author.send("This command require argument(s), you forgot to give, see `$help <command>` to see what argument it needs")
        await ctx.message.delete()
    else:
        await ctx.author.send(f"Sorry but i've encountered an error. My Owner was warned, he will investigate and fix me. Please be patient.")
        owner = (await bot.application_info()).owner
        await owner.send(f'{error.message}')
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.message.delete()

@bot.command()
async def log(ctx):
    try:
        owner = (await bot.application_info()).owner
        if ctx.author.id == owner.id:
            logger = logging.getLogger()
            level = logger.getEffectiveLevel()
            if level == logging.DEBUG:
                logger.setLevel(logging.ERROR)
                await owner.send('logging set to INFO')
            else:
                logger.setLevel(logging.DEBUG)
                await owner.send('logging set to DEBUG')
        else:
            await ctx.author.send('Nope')
    except Exception as err:
        logging.error(err)


@bot.command()
async def forceupdate(ctx):
    try:
        owner = (await bot.application_info()).owner
        if ctx.author.id == owner.id:
            query = db.query(Games)
            logging.info(query.count())
            if query.count()>0:
                for oGame in query.all():
                    if oGame.steam_id:
                        api = Steam(os.environ['STEAM_API_KEY'])
                        await asyncio.sleep(1)
                        gameInfos = api.get_game_info_from_store(oGame.steam_id)
                        if gameInfos is not None:
                            if 'categories' in gameInfos:
                                for category in gameInfos['categories']:
                                    if category['id'] in (1,9):
                                        logging.info('multiplayer detected')
                                        oGame.multiplayer = True
        else:
            ctx.author.send('your are not owner of the bot... GFY!')
    except Exception as err:
        logging.error(err)

@bot.event
async def on_ready():
    """ create server config if not already exist """
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{}help".format(default_prefix)))
    my_guilds = bot.guilds
    for guild in my_guilds:
        me_onguild = guild.me
        logging.info(f"connected to {guild.name} as {me_onguild}")

@bot.event
async def on_guild_join(self, guild):
    """ on join add default config for guild """
    try:
        query = db.query(Servers).filter(server_id=guild.id)
        if query.count() == 0:
            oServer = Servers(server_id=guild.id,prefix='$')
            db.add(oServer)
            db.commit()
        query = db.query(Servers).filter(server_id=guild.id)
        prefix = query.one().prefix
        """ on join add default config for user in guild """
        for member in guild.fetch_members:
            query = db.query(Users).filter(user_id == member.id)
            # If the user doesn't already exist in db, add it
            if query.count() == 0:
                oUser = Users(user_id=member.id,disallow_globally=False,disallow_users=None)
                db.add(oUser)
        #await guild.owner.send(f"Hello! i'm game matcher bot, i'm glad to work for your guild. You can use `{prefix}help` command to get more infos about me. See you soon! :)")
        owner = (await bot.application_info()).owner
        await owner.send(f"Hello! i'm game matcher bot, i'm glad to work for your guild. You can use `{prefix}help` command to get more infos about me. See you soon! :)")
    except Exception as err:
        logging.error(err)

@bot.event
async def on_member_update(before, after):
    """ listening when user is playing game """
    try:
        if not after.bot and after.activity:
            activity = after.activity
            logging.debug(f'detected {activity.name} activity for {after.display_name}@{after.id} on {after.guild}')
            if after.activity.type == discord.ActivityType.playing:
                if hasattr(activity, 'application_id'):
                    query = db.query(Games).filter(or_(Games.name == activity.name.lower(),Games.discord_id == activity.application_id))
                else:
                    query = db.query(Games).filter(Games.name == activity.name.lower())
                if query.count() == 0:
                    # add the game to database
                    if hasattr(activity, 'application_id'):
                        oGames = Games(name=activity.name.lower(), discord_id=activity.application_id)
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
                        oGames.discord_id=activity.application_id
                        db.commit()
                        db.refresh(oGames)

                # we don't save the fact than this user own the game if he didn't allow bot to do it
                query = db.query(Users).filter(Users.user_id == after.id)
                if query.count() > 0:
                    oUser = query.one()
                else:
                    oUser = Users(user_id=after.id)
                    db.add(oUser)
                    db.commit()
                    db.refresh(oUser)

                if not oUser.disallow_globally:
                    query = db.query(UserGames).filter(UserGames.game_id == oGames.game_id, UserGames.user_id == after.id)
                    if query.count() == 0:
                        db.add(UserGames(game_id=oGames.game_id, user_id=after.id))
                        db.commit()
                        logging.debug("@{} added {}".format(after.id, activity.name.lower()))
                    else:
                        logging.debug(f"@{after.id} already tied to {activity.name.lower()}")
                        """else: bugged
                        oGamesOwned = query.one()
                        oGamesOwned.last_played_at = datetime.datetime.utcnow()
                        db.commit()"""
    except Exception as err:
        logging.error(err)

@bot.command()
async def infos(ctx):
    """ Get versions, github and support link """
    await ctx.channel.send(
        """
Games-Matcher v{0},
informations and support: https://github.com/dbuteau/games-matcher
You can offer me a beer as thank via <https://paypal.me/DanielButeau>
        """
        .format(version)
    )

bot.run(os.environ['DISCORD_TOKEN'])
