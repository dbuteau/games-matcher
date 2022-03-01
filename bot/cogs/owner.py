import os,sys

from sqlalchemy.sql.sqltypes import Boolean
import discord
import logging
import re
from discord.ext import commands
from discord.utils import get
from libs.models import Games, UserGames
from libs.interntools import interntools


class SuperAdmin(commands.Cog):
    """ Only Bot owner commands """
    def __init__(self, bot, db):
        self._logger = logging.getLogger('discord')
        self._bot = bot
        self._db = db

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.guild_only()
    async def clear(self, ctx):
        """" delete all bot mast message from channel """
        try:
            channel = ctx.channel
            async for message in channel.history(limit=50):
                if message.author == ctx.me:
                    await message.delete()
                elif re.match(r"" + re.escape(ctx.prefix) +".*", message.content, re.I):
                    await message.delete()
        except Exception as err:
            self._logger.error(f'clear cmd raised exception at line {sys.exc_info()[-1].tb_lineno}; {err}')

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def log(self, ctx, new_level=None):
        """ switch logs level to DEBUG/ERROR """
        try:
            level = self._logger.getEffectiveLevel()
            if new_level:
                if new_level == 'debug':
                    self._logger.setLevel(logging.DEBUG)
                elif new_level == 'info':
                    self._logger.setLevel(logging.INFO)
                elif new_level == 'warning':
                    self._logger.setLevel(logging.WARNING)
                elif new_level == 'error':
                    self._logger.setLevel(logging.ERROR)
            elif level == logging.DEBUG:
                self._logger.setLevel(logging.ERROR)
                await ctx.author.send('logging set to INFO')
            else:
                self._logger.setLevel(logging.DEBUG)
                await ctx.author.send('logging set to DEBUG')
            self._logger.info(f'set log level to {self._logger.getEffectiveLevel()}')
        except Exception as err:
            self._logger.error(err)
            raise Exception('log command failed') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def users(self, ctx):
        try:
            query = self._db.query(UserGames.user_id).distinct()
            users = []
            if query.count() > 0:
                for user in query.all():
                    self._logger.info(f'{user.user_id} is {get(self._bot.get_all_members(), id=user.user_id)}')
                    users.append(f'{user.user_id} is {get(self._bot.get_all_members(), id=user.user_id)}')
                await interntools.paginate(ctx, users, f'Total users {query.count()}', remove_reaction=False, limit=20)
            else:
                ctx.author.send('None returned')
        except Exception as err:
            self._logger.info(f'{err}')

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def gamesof(self, ctx, member: discord.Member):
        try:
            query = self._db.query(Games.name).filter(Games.game_id == UserGames.game_id, UserGames.user_id == member.id)
            embed = discord.Embed(title=f'{member.display_name}@{member.id} games:')
            embed.add_field(name="Games", value=query.all())
            result = []
            for game in query.all():
                result.append(f'{game.name}')
            if query.count() > 0:
                header = f'{member.display_name} have {query.count()} games:'
                await interntools.paginate(ctx, result, header=header)
            else:
                ctx.author.send('None returned')
        except Exception as err:
            raise Exception(f'gamesof for {member.display_name}@{member.id} - {err}') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def games_search(self, ctx, game_name):
        """ search for game by its name use % for wildcard """
        try:
            query = self._db.query(Games.game_id,Games.steam_id).filter(Games.game_name == game_name)
            embed = discord.Embed(title=f'result for:{game_name}')
            embed.add_field(name="found", value=query.all())
            result = []
            for game in query.all():
                result.append(f'{game.id}  {game.name}')
            if query.count() > 0:
                await interntools.paginate(ctx, result)
            else:
                ctx.author.send('None returned')
        except Exception as err:
            raise Exception(f'game search "{game_name}" - {err}') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def games_wo_info(self, ctx):
        """ search for games with multiplayer info set to none"""
        try:
            query = self._db.query(Games.game_id, Games.name, Games.steam_id).filter(Games.multiplayer == None)
            embed = discord.Embed(title='Games without multiplayer infos')
            embed.add_field(name="Games", value=query.all())
            result = []
            for game in query.all():
                result.append(f'#{game.game_id} - steam:{game.steam_id} - {game.name}')
            if query.count() > 0:
                header = f'Nb games: {query.count()}'
                await interntools.paginate(ctx, result, header=header)
            else:
                ctx.author.send('None returned')
        except Exception as err:
            raise Exception(f'games_wo_info - {err}') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def game_is_mp(self, ctx, game_id):
        """ defining the game 'game_id' as multiplayer """
        query = self._db.query(Games).filter(Games.game_id == game_id)
        gameindb = query.one()
        gameindb.multiplayer = True
        self._db.commit()
        
    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def game_is_solo(self, ctx, game_id):
        """ defining the game 'game_id' as solo  """
        query = self._db.query().filter(Games.game_id == game_id)
        gameindb = query.one()
        gameindb.multiplayer = True
        self._db.commit()

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def whois(self, ctx, member: discord.Member):
        try:
            await ctx.author.send(f'{member.display_name}@{member.id}')
        except Exception as err:
            self._logger.error(err)
            raise Exception('whois command failed') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def msg(self, ctx, member: discord.Member):
        raise NotImplementedError

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def banserv(self,ctx):
        raise NotImplementedError

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def banperson(self,ctx):
        raise NotImplementedError