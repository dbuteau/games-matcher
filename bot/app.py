# coding: utf-8

"""
This Bot found game in common between 2 member
"""
import os
import sys
import datetime
import logging
import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Users, Games, UserGames, Servers, Base

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

engine = create_engine('sqlite:///games-matcher-bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.typing = False
bot = commands.Bot('$', intents=intents)

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
async def on_ready():
    """ create server config if not already exist """
    my_guilds = bot.guilds
    for guild in my_guilds:
        me_onguild = guild.me
        logging.debug(me_onguild)
    logging.info('logged in as {0.user}'.format(bot))


@bot.event
async def on_member_update(before, after):
    """ listening when user is playing game """
    logging.info('on_member_update detected')
    try:
        if not after.bot and after.activity:
            activity = after.activity
            if after.activity.type == discord.ActivityType.playing:
                query = db.query(Games).filter(Games.name == activity.name)
                if query.count() == 0:
                    # add the game to database
                    oGames = Games(name=activity.name, application_id=activity.application_id)
                    db.add(oGames)
                    db.commit()
                    db.refresh(oGames)
                elif query.count() > 1:
                    raise RuntimeError('Duplicate game')
                else:
                    oGames = query.one()

                query = db.query(UserGames).filter(UserGames.game_id == oGames.game_id, UserGames.user_id == after.id)
                if query.count() == 0:
                    db.add(UserGames(game_id=oGames.game_id, user_id=after.id))
                    db.commit()
                else:
                    oGamesOwned = query.one()
                    oGamesOwned.last_played_at = datetime.datetime.utcnow()
                    db.commit()
    except Exception as err:
        logging.error(err)


@bot.command(name='import', description='test')
async def import_games(ctx):
    """ importing your owned games into db """
    try:
        if ctx.message.attachments:
            attached_file = await ctx.message.attachments[0].read()
            row_objects = []
            row_number = 0
            for line in attached_file.split(b'\n'):
                game_name = line.decode('Windows-1252').rstrip().replace('_', ' ').lower()
                query = db.query(Games).filter(Games.name == game_name)
                if query.count() == 0:
                    oGame = Games(name=game_name)
                    # check if we don't try to duplicate in the same request
                    duplicate = False
                    for row in row_objects:
                        if oGame.name == row.name:
                            duplicate = True
                    # add the game to database
                    if not duplicate:
                        row_objects.append(oGame)
                        row_number += 1
                elif query.count() > 1:
                    raise RuntimeError('Duplicate game')
            # need to commit at end all in once bc of harddisk write limitations
            db.bulk_save_objects(row_objects)
            db.commit()
            await ctx.author.send('{0} games unknown added to our base.'.format(row_number))

            row_objects = []
            row_number = 0
            for line in attached_file.split(b'\n'):
                game_name = line.decode('Windows-1252').rstrip().replace('_', ' ').lower()
                query = db.query(Games).filter(Games.name == game_name)
                if query.count() == 1:
                    oGames = query.one()
                    oGamesOwned = db.query(UserGames).filter(UserGames.game_id == oGames.game_id, UserGames.user_id == ctx.author.id)
                    if oGamesOwned.count() == 0:
                        uGame = UserGames(game_id=oGames.game_id, user_id=ctx.author.id)
                        duplicate = False
                        for row in row_objects:
                            if uGame.game_id == row.game_id and uGame.user_id == row.user_id:
                                duplicate = True
                        if not duplicate:
                            row_objects.append(uGame)
                            row_number += 1
            db.bulk_save_objects(row_objects)
            db.commit()
            await ctx.author.send('{0} games linked to your account'.format(row_number))

    except Exception as err:
        exc_type, exc_obj, tb = sys.exc_info()
        await report_error(ctx, err, tb.tb_lineno)


@bot.command(name='MyTop')
async def my_list(ctx):
    """ get list of all games you own """
    my_games = db.query(Games.name).join(UserGames).filter(UserGames.user_id == ctx.author.id).order_by(UserGames.last_played_at.desc()).limit(20)
    if my_games.count() > 0:
        game_list = []
        for game in my_games.all():
            logging.info(game.name)
            game_list.append(game.name)
        #await ctx.author.send('\n'.join(game_list))
        await ctx.channel.send('\n'.join(game_list))
    else:
        await ctx.channel.send("Sorry i don't have data about you. Try to use import command, or play games i will remember it")


@bot.command()
async def privacy(ctx):
    """ read what kind of data the bot collect about you """
    text = """**Data we collect**
    The bot collect your discord_id, your last activity on game and the fact than you own a game.
    In add the bot create data about your privacy preferences (disallow/block).
    As you can block members of a server asking about your data, we keep server id you are member of.

    **Why we need this data?:**
        - discord id is necessary to keep trace of who own which games
        - your last activity is necessary when answering to sort games with most recent played first
        - the servers you are members of, to keep trace if you want to disallow members of this servers to access your data

    **Why the bot collect your gaming activity?**
    For two reasons:
        - Populate our database games list with games we don't know.
        When you use delete command, this data will not be deleted because this data are not tied to you, it's anonymously registered in our data.
        - Auto complete your list of owned game. When you use the delete command, this datas are deleted

    **I want bot forget about me. How i do that?**
    1/ First use `delete` command to erase our database from data we know about you
    2/ then use `disallow` command saying bot to stop collecting your playing activity.
    Unfortunatly, to remember you don't want bot collect data about you we need at minimum your discord_id, but it's all we will keep from you.

    **Warnings :**
        - `delete` command delete all your privacy configuration, the fact you disallowed or blocked members will be erased. Disallowing before delete is useless.
        - `delete` command delete all data about you, cross server or guild. So if you delete on server X, your datas will be erase for all other servers too.
    """
    await ctx.author.send(text)


@bot.command()
async def delete(ctx):
    """ delete all data we know about you """
    query = db.query(UserGames).filter(UserGames.user_id == ctx.author.id).delete()
    query = db.query(Users).filter(Users.user_id == ctx.author.id).delete()
    db.commit()
    await ctx.channel.send('Done! Everything is wiped!')

bot.run(os.environ['DISCORD_TOKEN'])
