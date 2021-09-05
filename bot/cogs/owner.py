import os,sys
import discord
import logging
from discord.ext import commands
from discord.utils import get
from libs.models import Games, UserGames
from libs.interntools import interntools


class SuperAdmin(commands.Cog):
    """ Only Bot owner commands """
    def __init__(self, bot, db):
        self.logger = logging.getLogger('discord')
        self.bot = bot
        self.db = db

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def log(self, ctx, new_level=None):
        """ switch logs level to DEBUG/ERROR """
        try:
            level = self.logger.getEffectiveLevel()
            if new_level:
                if new_level == 'debug':
                    self.logger.setLevel(logging.DEBUG)
                elif new_level == 'info':
                    self.logger.setLevel(logging.INFO)
                elif new_level == 'warning':
                    self.logger.setLevel(logging.WARNING)
                elif new_level == 'error':
                    self.logger.setLevel(logging.ERROR)
            elif level == logging.DEBUG:
                self.logger.setLevel(logging.ERROR)
                await ctx.author.send('logging set to INFO')
            else:
                self.logger.setLevel(logging.DEBUG)
                await ctx.author.send('logging set to DEBUG')
            self.logger.info(f'set log level to {self.logger.getEffectiveLevel()}')
        except Exception as err:
            self.logger.error(err)
            raise Exception('log command failed') from err

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def users(self, ctx):
        try:
            query = self.db.query(UserGames.user_id).distinct()
            users = []
            if query.count() > 0:
                for user in query.all():
                    self.logger.info(f'{user.user_id} is {get(self.bot.get_all_members(), id=user.user_id)}')
                    users.append(f'{user.user_id} is {get(self.bot.get_all_members(), id=user.user_id)}')
                await interntools.paginate(ctx, users, f'Total users {query.count()}', remove_reaction=False, limit=20)
            else:
                ctx.author.send('None returned')
        except Exception as err:
            self.logger.info(f'{err}')

    @commands.command(pass_context=True)
    @commands.is_owner()
    @commands.dm_only()
    async def gamesof(self, ctx, member: discord.Member):
        try:
            logging.error('debug')
            query = self.db.query(Games.name).filter(Games.game_id == UserGames.game_id, UserGames.user_id == member.id)
            embed = discord.Embed(title=f'{member.display_name}@{member.id} games:')
            embed.add_field(name="Games", value=query.all())
            await ctx.author.send(embed=embed)
        except Exception as err:
            raise Exception(f'gamesof for {member.display_name}@{member.id} - {err}') from err