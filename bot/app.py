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

version = '0.0.1'
default_prefix = '$'

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

engine = create_engine('sqlite:///games-matcher-bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.typing = False
bot = commands.Bot(default_prefix, intents=intents)

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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="{}help".format(default_prefix)))
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
                query = db.query(Games).filter(Games.name == activity.name.lower())
                if query.count() == 0:
                    # add the game to database
                    oGames = Games(name=activity.name.lower(), application_id=activity.application_id)
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


def extract_from_file(attached_file):
    rows = []
    for line in attached_file.split(b'\n'):
        # convert non utf8 chars
        line = line.decode('Windows-1252')
        # the line should contain only one ; if not there is a problem
        if line.count(';') > 1:
            logging.error("This fucking game name contain ';': {0}".format(line))
            return False
        name, activity = line.split(';')
        game_name = name.rstrip().replace('_', ' ').lower()
        activity = activity.rstrip()
        if activity != 'None':
            activity = datetime.datetime.strptime(activity, '%d/%m/%Y %H:%M:%S')
        else:
            activity = None
        rows.append({'name': game_name, 'activity': activity})
    return rows


@bot.command(name='import', description='test')
async def import_games(ctx):
    """ importing your owned games into db. Attache the csv file to your command."""
    try:
        if ctx.message.attachments:
            attached_file = await ctx.message.attachments[0].read()
            rows = extract_from_file(attached_file)
            row_objects = []
            for row in rows:
                query = db.query(Games).filter(Games.name == row['name'])
                if query.count() == 0:
                    oGame = Games(name=row['name'])
                    # check if we don't try to duplicate in the same request
                    duplicate = False
                    for row in row_objects:
                        if oGame.name == row.name:
                            duplicate = True
                    # add the game to database
                    if not duplicate:
                        row_objects.append(oGame)
                elif query.count() > 1:
                    raise RuntimeError('Duplicate game')
            # need to commit at end all in once bc of harddisk write limitations
            db.bulk_save_objects(row_objects)
            db.commit()
            await ctx.author.send('{0} games unknown added to our base.'.format(len(row_objects)))

            row_objects = []
            for row in rows:
                query = db.query(Games).filter(Games.name == row['name'])
                if query.count() == 1:
                    oGames = query.one()
                    oGamesOwned = db.query(UserGames).filter(UserGames.game_id == oGames.game_id, UserGames.user_id == ctx.author.id)
                    if oGamesOwned.count() == 0:
                        uGame = UserGames(game_id=oGames.game_id, user_id=ctx.author.id, last_played_at=row['activity'])
                        duplicate = False
                        for row in row_objects:
                            if row.game_id == uGame.game_id and row.user_id == uGame.user_id:
                                duplicate = True
                        logging.error('duplicate is defined to {}'.format(str(duplicate)))
                        if not duplicate:
                            row_objects.append(uGame)
                elif query.count() > 1:
                    raise RuntimeError(query.all()[0].name)
            if len(row_objects) > 0:
                db.bulk_save_objects(row_objects)
                db.commit()
            await ctx.author.send('%s games linked to your account' % len(row_objects))
        else:
            ctx.channel.send('You forget to attach file to your command')
    except RuntimeError as err:
        logging.error('Duplicates are detected in DATABASE: %s' % err)
    except ValueError as err:
        exc_type, exc_obj, tb = sys.exc_info()
        logging.error(tb.tb_lineno, err)
        if err == 'too many values to unpack':
            logging.error('Too many values to unpack')
            await ctx.channel.send('It seems than your file have game name with semi-colon in it, try to delete this char from the name. A report of this problem was raise at bot owner')
    except Exception as err:
        exc_type, exc_obj, tb = sys.exc_info()
        await report_error(ctx, err, tb.tb_lineno)


@bot.command(name='mytop')
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
        await ctx.channel.send(
            "Sorry i don't have data about you. Try to import games from file, or play games i will remember it. Type `{0}help` command for more informations"
            .format(default_prefix))


@bot.command()
async def match(ctx, member: discord.Member):
    """ Found 20th games in common ordered by last activity """
    """ TODO """
    your_games = db.query(Games, UserGames).filter(UserGames.user_id == ctx.author.id)
    his_games = db.query(Games, UserGames).filter(UserGames.user_id == member.id)
    common_games = your_games.union(his_games)
    query4 = db.query(Games).join(common_games).order_by(UserGames.last_played_at.desc()).limit(20).all
    games_list = []
    for game in query4:
        games_list.append(game.name)
    msg = '{0} and you have this games in common:\n'.format(member.display_name)
    msg += '\n'.join(games_list)
    await ctx.author.send(msg)


@bot.command()
async def find(ctx, game_name):
    """ find 20 member which own the game """
    member_list = []
    users = db.query(UserGames.user_id).join(Games).filter(Games.name == game_name.lower()).all()
    for user in users:
        if not user.user_id == ctx.author.id:
            member = discord.utils.find(lambda m: m.id == user.user_id, ctx.author.channel.guild.members)
            if member:
                member_list.append(member.display_name)
    if len(member_list) > 0:
        await ctx.author.send('\n'.join(member_list))
    else:
        await ctx.author.send('No one found on the server')


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
        When you use delete command, this data will not be deleted because this data are not tied to you, it's anonymously registered in our database.
        - Auto complete your list of owned game. When you use the delete command, this datas are deleted. You can avoid this collect using `disallow` command

    **I want bot forget about me. How i do that?**
    1/ First use `delete` command to erase our database from data we know about you
    2/ then use `disallow` command saying bot to stop collecting your playing activity.
    Unfortunatly, to remember than you don't want bot collect data about you we need at minimum your discord_id, but it's all we will keep from you.

    **Warnings :**
        - `delete` command delete all your privacy configuration, the fact you disallowed or blocked members will be erased. Disallowing before delete is useless.
        - `delete` command delete all data about you, cross server or guild. So if you delete on server X, your datas will be erased for all other servers too.
    """
    await ctx.author.send(text)


@bot.command()
async def delete(ctx):
    """ delete all data we know about you """
    query = db.query(UserGames).filter(UserGames.user_id == ctx.author.id).delete()
    query = db.query(Users).filter(Users.user_id == ctx.author.id).delete()
    db.commit()
    await ctx.channel.send('Done! Everything is wiped!')


@bot.command()
async def disallow(ctx):
    """ the bot stop to listen your activity """
    query = db.query(Users).get(ctx.author.id).one()
    if query.disallow_globally:
        oUser = Users(disallow_globally=False)
        await ctx.channel.send('Your Activity collect is now reactivated')
    else:
        oUser = Users(disallow_globally=True)
        await ctx.channel.send('Your Activity collect is now disallowed')
    db.commit()


@bot.command()
async def block(ctx, member: discord.Member):
    """ block the user to aks for your game owned """
    """ TODO """
    pass


@bot.command()
async def unblock(ctx, member: discord.Member):
    """ unblock the user you previously blocked """
    """ TODO """
    pass

@bot.command()
async def infos(ctx):
    """ Get versions, github and support link """
    ctx.channel.send(
        """
        Games-Matcher v{0}
        source: https://github.com/dbuteau/games-matcher
        support: https://github.com/dbuteau/games-matcher/issues
        """
        .format(version)
    )

bot.run(os.environ['DISCORD_TOKEN'])
