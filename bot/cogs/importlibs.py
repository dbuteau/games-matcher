import os
import sys
import discord
import dateutil.parser
import locale
import logging
import re 
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from sqlalchemy import or_
from libs.api.steam import Steam
from libs.models import Games, UserGames


class Import(commands.Cog, name='Direct messages commands'):
    self = None

    def __init__(self, bot, db):
        self.cog_name = 'Commands'
        self._bot = bot
        self._db = db
        self.logger = logging.getLogger('discord')

    @commands.group(
        name='import',
        brief='See `help import` in private message with bot',
        description='Import from your online library list '
                    'of your owned games.\nYour library need to be set as public.\nSyntax:',
        usage='subcommand library_id')
    async def library(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Subcommand is missing. Type `{self._bot.command_prefix()}help import` for details')

    async def get_gameinfos(self, steam_id):
        try:
            result = False
            api = Steam(os.environ['STEAM_API_KEY'])
            gameInfos = api.get_game_info_from_store(steam_id)
            if gameInfos is not None:
                result = {}
                result['multiplayer'] = False
                if gameInfos['categories']:
                    for category in gameInfos['categories']:
                        if category['id'] in (1, 9, 36, 38):
                            self.logger.debug(f"{gameInfos['name']} is multiplayer")
                            result['multiplayer'] = True
                if gameInfos['release_date']['date'] != '':
                    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
                    if bool(re.search('[\u0400-\u04FF]', gameInfos['release_date']['date'])):
                        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
                    result['release_date'] = dateutil.parser.parse(gameInfos['release_date']['date'])
                    self.logger.info(f"{gameInfos['release_date']['date']} converted to {result['release_date']}")
                else:
                    self.logger.info(f"[{gameInfos['name']}#{steam_id}] {gameInfos['release_date']} return is none")
                    result['release_date'] = None
            return result
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.logger.error(f'{fname}({exc_tb.tb_lineno}): ID {steam_id} - {err}')

    @library.command(usage='your_steam_id')
    @commands.max_concurrency(1, per=BucketType.default, wait=True)
    @commands.dm_only()
    async def steam(self, ctx, user_steam_id):
        """ Import the `steam_id` Steam library. """
        try:
            owner = (await ctx.bot.application_info()).owner
            self.logger.info(f'start Import of steam lib for {ctx.author.id}')
            await ctx.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name="importing steam lib"))

            api = Steam(os.environ['STEAM_API_KEY'])
            raw_data = api.get_User_Owned_Games(user_steam_id)
            counter = {'imported': 0, 'multi': 0}

            embed = discord.Embed(title=f'{api.whoIimport} Steam Lib import in progress')
            embed.add_field(name='Total Games found', value=raw_data['response']['game_count'])
            embed.add_field(name='Processed Games:', value=counter['imported'])
            embed.add_field(name='Multiplayer Games:', value=counter['multi'])

            progress = await ctx.author.send(embed=embed)
            for game in raw_data['response']['games']:
                oGame = Games(name=game['name'].lower(), steam_id=game['appid'], multiplayer=False)

                # check if the game is already in db search by id or by name,
                # should return only one row in anycase else there is problem
                query = self._db.query(Games).filter(Games.steam_id == oGame.steam_id)
                if query.count() == 0:
                    query = self._db.query(Games).filter(Games.name == oGame.name)
                

                # if we miss some game info, then we ask steam store for it,
                # warning the api is very sensible to 'too much request'
                gameInfos = None
                if query.count() > 1:
                    # if more than one row is found, need human investigation
                    err = f"game_id={oGame.steam_id} name={oGame.name} got possible duplicate"
                    raise Exception from err
                if query.count() == 1 and query.one().multiplayer:
                    counter['multi'] += 1
                else:
                    await asyncio.sleep(1)
                    details = await self.get_gameinfos(oGame.steam_id)
                    if details:
                        oGame.release_date = details['release_date']
                        oGame.multiplayer = details['multiplayer']
                    else:
                        self.logger.info(f"{game['name'].lower()} not found in steam store")
                        await ctx.author.send(f"{oGame.name} - not found in steam store API(ID:{oGame.steam_id})")

                    if query.count() == 0:
                        # insert into db if not exist
                        self._db.add(oGame)
                        self._db.commit()
                        self.logger.info(f"add {oGame.name} game to database")
                    elif query.count() == 1:
                        gameindb = query.one()
                        gameindb.steam_id = oGame.steam_id
                        if gameInfos is not None and gameindb.multiplayer is None:
                            gameindb.multiplayer = oGame.multiplayer
                        self._db.commit()
                        self.logger.info(f"update game #{gameindb.game_id}/{oGame.steam_id}: {oGame.name}")

                # refresh request
                oGame = query.one()
                self._db.refresh(oGame)

                # Once we are sure the game exist in db, tie it to user profil
                if oGame.multiplayer:
                    query = self._db.query(UserGames)\
                        .filter(
                            UserGames.game_id == oGame.game_id,
                            UserGames.user_id == ctx.author.id)
                    if query.count() == 0:
                        oUserGame = UserGames(game_id=oGame.game_id, user_id=ctx.author.id, last_played_at=None)
                        self._db.add(oUserGame)
                        self._db.commit()
                counter['imported'] += 1

                # update embeded message
                embed.set_field_at(1, name='Processed Games:', value=counter['imported'])
                embed.set_field_at(2, name='Multiplayer Games:', value=counter['multi'])
                await progress.edit(embed=embed)
        except Exception as err:
            await owner.send(f"{oGame.name} - err")
            await ctx.author.send(f"{oGame.name} - Encountered exception, the dev has been notified")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception from err

    @library.command(name='gog', hidden=True)
    @commands.max_concurrency(1, per=BucketType.default, wait=True)
    @commands.dm_only()
    async def gog(self, ctx, user_id):
        """ import your GOG library """
        raise NotImplementedError

    @library.command()
    @commands.is_owner()
    @commands.dm_only()
    async def forceupdate(self, ctx, criteria: str):
        """ scan for date|multiplayer column = None and fill with store api """
        try:
            if criteria == 'date':
                query = self._db.query(Games)\
                    .filter(
                        Games.multiplayer.is_(True),
                        Games.release_date is None,
                        Games.steam_id is not None)
            elif criteria == 'multi':
                query = self._db.query(Games)\
                    .filter(
                        Games.multiplayer.is_(True),
                        Games.steam_id is not None,
                        or_(
                            Games.release_date is None,
                            Games.release_date.is_(False)))
            else:
                raise UserWarning("choose between 'date' or 'multi'")
            self.logger.debug(f'query found {query.count()}')
            if query.count() > 0:
                for oGame in query.all():
                    await asyncio.sleep(1)
                    logging.info(f'object: {oGame}')
                    self.logger.debug(f'interrogate steam store for {oGame.name}#{oGame.steam_id}')
                    details = await self.get_gameinfos(oGame.steam_id)
                    if details is not None:
                        if 'release_date' in details:
                            oGame.release_date = details['release_date']
                        if 'multiplayer' in details:
                            oGame.multiplayer = details['multiplayer']
                        self._db.commit()
                        self.logger.debug(
                            f'{oGame.name} updated with release_date: '
                            '{oGame.release_date} multiplayer: {oGame.multiplayer}')
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception from err
