import os
import discord
import datetime
import time
import logging
import asyncio
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from libs.models import Users, Games, UserGames
from libs.steam import Steam
from sqlalchemy import or_

class Import(commands.Cog):
    """ Private message only, write $help wit bot private message to see more info """
    def __init__(self, bot, db):
        self._bot = bot
        self._db = db

    @commands.command()
    @commands.max_concurrency(1, per=BucketType.default, wait=True)
    @commands.dm_only()
    async def steam(self, ctx, user_steam_id):
        """ Import your steam library (send direct message to bot)"""
        try:
            logging.info(f'start Import of steam lib for {ctx.author.id}')

            api = Steam(os.environ['STEAM_API_KEY'])
            raw_data = api.get_User_Owned_Games(user_steam_id)
            if not raw_data:
                raise UserWarning("I can't read your steam library. Please put your games lib on steam as public")
            await ctx.author.send(f"We found {raw_data['response']['game_count']} games in your lib, it will take some time for extract infos from steam without get banned. Get you a coffee")
            counter = 0
            progress = await ctx.author.send(f"{counter}/{raw_data['response']['game_count']} processed")
            for game in raw_data['response']['games']:
                oGame = Games(name=game['name'].lower(), steam_id=game['appid'], multiplayer=False)

                # check if the game is already in db search by id or by name, should return only one row in anycase else there is problem
                query = self._db.query(Games).filter(or_(Games.steam_id == oGame.steam_id, Games.name == oGame.name))

                # if we miss some game info, then we ask steam store for it, warning the api is very sensible to 'too much request'
                gameInfos = None
                if query.count() == 0 or (query.count() == 1 and query.one().multiplayer is None):
                    await asyncio.sleep(1)
                    gameInfos = api.get_game_info_from_store(oGame.steam_id)
                    if gameInfos is None:
                        # await ctx.author.send(f"{oGame.name} no more exist in steam store")
                        pass
                    else:
                        if 'categories' in gameInfos:
                            for category in gameInfos['categories']:
                                if category['id'] in (1,9):
                                    logging.info('multiplayer detected')
                                    oGame.multiplayer = True
                if query.count() == 0:
                    # insert into db if not exist
                    logging.info(f"add {oGame.name} game to database")
                    self._db.add(oGame)
                    self._db.commit()
                elif query.count() == 1 and (gameInfos is not None):
                    gameindb = query.one()
                    gameindb.steam_id = oGame.steam_id
                    gameindb.multiplayer = oGame.multiplayer
                    self._db.commit()
                    logging.info(f"update game #{gameindb.game_id}/{oGame.steam_id}: {oGame.name}")
                elif query.count() > 1:
                    # if more than one row is found, need human investigation
                    logging.error(f"game_id={oGame.steam_id} name={oGame.name} got possible duplicate")
                    raise UserWarning(f"An Error occured with the game '{oGame.name}', my master was warned to investigate on it")

                # refresh request
                oGame = query.one()
                self._db.refresh(oGame)

                if oGame.multiplayer is None:
                    raise UserWarning('Game was not updated')

                # Once we are sure the game exist in db, tie it to user profil
                if oGame.multiplayer:
                    query = self._db.query(UserGames).filter(UserGames.game_id == oGame.game_id, UserGames.user_id == ctx.author.id)
                    if query.count() == 0:
                        oUserGame = UserGames(game_id=oGame.game_id, user_id=ctx.author.id, last_played_at=None)
                        self._db.add(oUserGame)
                        self._db.commit()
                counter += 1
                await progress.edit(content=f"{counter}/{raw_data['response']['game_count']} processed")
        except UserWarning as err:
            await ctx.author.send(f"{oGame.name} - {err}")
        except Exception as err:
            logging.error(f'{err}')
            raise Exception from err

