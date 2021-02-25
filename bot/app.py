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
from discord.ext import commands
from cogs import matcher, gImport, privacy
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from libs.models import Users, Games, UserGames, Servers, Base, WhosUp
from  libs.interntools import interntools

fo = open("version", "r")
version = fo.readline()

default_prefix = '$'

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
async def on_command_error(ctx,error):
    await ctx.message.delete()
    if isinstance(error, commands.MaxConcurrencyReached):
        await ctx.author.send('Bot is busy! Please retry in a minute')
        return
    else:
        owner = (await bot.application_info()).owner
        await owner.send(error)


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
    await guild.owner.send(f"Hello! i'm game matcher bot, i'm glad to work for your guild. You can use `{prefix}help` command to get more infos about me. See you soon! :)")

@bot.event
async def on_member_update(before, after):
    """ listening when user is playing game """
    try:
        logging.info(f'Detected activity of {after.id}')
        if not after.bot and after.activity:
            activity = after.activity
            logging.info('detected @{} on {}'.format(after.id, activity.name))
            if after.activity.type == discord.ActivityType.playing:
                query = db.query(Games).filter(or_(Games.name == activity.name.lower(),Games.discord_id == activity.application_id))
                if query.count() == 0:
                    # add the game to database
                    oGames = Games(name=activity.name.lower(), discord_id=activity.application_id)
                    db.add(oGames)
                    db.commit()
                    db.refresh(oGames)
                elif query.count() > 1:
                    raise RuntimeError('Duplicate game')
                else:
                    oGames = query.one()
                    oGames.discord_id=activity.application_id
                    db.commit()
                    db.refresh(oGames)

                # we don't save the fact than this user own the game if he didn't allow bot to do it
                query = db.query(Users).filter(Users.user_id).one()
                if not query.disallow_globally:
                    query = db.query(UserGames).filter(UserGames.game_id == oGames.game_id, UserGames.user_id == after.id)
                    if query.count() == 0:
                        db.add(UserGames(game_id=oGames.game_id, user_id=after.id))
                        db.commit()
                    else:
                        oGamesOwned = query.one()
                        oGamesOwned.last_played_at = datetime.datetime.utcnow()
                        db.commit()
                    logging.info("@{} added {}".format(after.id, activity.name.lower()))
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
