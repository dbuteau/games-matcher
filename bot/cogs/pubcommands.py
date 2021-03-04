import os, sys
import logging
from datetime import date
import re
import discord
from discord.ext import commands
from libs.interntools import interntools
from libs.models import (
    Games,
    UserGames)
from sqlalchemy import (
    func,
    desc
)

class Commands(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.command()
    @commands.guild_only()
    async def top(self,ctx, Number=10):
        """ number : Show Top {number} games owned by server members (10 by default)"""
        try:
            members = ctx.guild.members
            members_id = []
            for member in members:
                members_id.append(member.id)
            query = self.db.query(Games.name, func.count(UserGames.game_id).label("Nb")) \
                .group_by(UserGames.game_id) \
                .filter(Games.game_id==UserGames.game_id, UserGames.user_id.in_((members_id)), Games.multiplayer==True) \
                .order_by(desc('Nb')) \
                .limit(Number)
            result = []
            for game in query.all():
                result.append(f'{game.name} ({game.Nb})')

            header = f'List of {Number} games with most players:'
            await interntools.paginate(ctx, result, header=header)
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception from err

    @commands.command()
    @commands.guild_only()
    async def match(self, ctx, member: discord.Member):
        """ @user : Find commons game between you and @user """
        try:
            logging.info(f'try to found common game between {ctx.author.id} and {member.id}')
            """ Found games in common with <member> ordered by last activity """
            query_result = self.db.query(Games).join(UserGames).filter(Games.game_id == UserGames.game_id, UserGames.user_id == ctx.author.id ).order_by(desc(Games.release_date)).all()
            your_games = []
            for game in query_result:
                your_games.append(game.name)

            query_result = self.db.query(Games).join(UserGames).filter(Games.game_id == UserGames.game_id, UserGames.user_id == member.id ).order_by(desc(Games.release_date)).all()
            his_games = []
            for game in query_result:
                his_games.append(game.name)
            logging.info(f'your_games: {your_games}, his_games: {his_games}')

            commons_games = list(set(your_games).intersection(his_games))
            logging.info(f'common games: {commons_games}')

            if len(commons_games) > 0:
                header = '{0} and you have {1} games in common:'.format(member.display_name,len(commons_games))
                await interntools.paginate(ctx, commons_games, header=header)
            else:
                await ctx.channel.send('No games in common found')
        except Exception as err:
            logging.info(f'Match command raised and exception; {err}')


    @commands.command()
    @commands.guild_only()
    async def find(self, ctx, *, game_name: str):
        """ game_name : find members which own the 'game name' """
        nl = "\n"
        try:
            member_list = []
            embed = discord.Embed(title=f'Search Members owning "{game_name}"')
            search = game_name.lower()
            users = self.db.query(UserGames.user_id).join(Games).filter(Games.name==search).all()
            for user in users:
                if not user.user_id == ctx.author.id:
                    member = discord.utils.find(lambda m: m.id == user.user_id, ctx.guild.members)
                    if member:
                        member_list.append(member.display_name)
            if len(member_list) > 0:
                embed.add_field(name=f'Result', value='\n'.join(member_list))
            else:
                embed.add_field(name="Result", value='Sorry found no one here owning this game')
            await ctx.channel.send(embed=embed)
        except commands.NoPrivateMessage :
            await ctx.author.send("This command need to be send in guild channel only, not in private message")
            pass
        except Exception as err:
            logging.info(f'Match command raised and exception; {err}')

    @commands.command()
    @commands.guild_only()
    async def up(self, ctx, time=30):
        """ time : Signal you are up for game session, the offer expire in <time> minutes (30 by default)"""
        header = f'{ctx.author.name} is ready to play'
        footer = f"\n*Say to other you want to play too by writing `{ctx.prefix}up` command!*"
        nl = '\n'

        now = datetime.datetime.now()
        query1 = self.db.query(WhosUp).filter(WhosUp.expire_at > now)
        # get list of other players up too
        if query1.count() > 0:
            players_waiting = query1.all()
            players_list = []
            for player in players_waiting:
                if player.user_id != ctx.author.id:
                    member = discord.utils.find(lambda m: m.id == player.user_id, ctx.guild.members)
                    players_list.append(member.display_name)
            if len(listing) > 0:
                header += f" like {len(listing)} others"
            else:
                header += ' but is alone :sob:'
        # add the player to the WhosUp list
        query2 = self.db.query(WhosUp).filter(WhosUp.user_id==ctx.author.id)
        expire_at = datetime.datetime.now() + datetime.timedelta(minutes=int(time))
        if query2.count() == 0:
            myStatus = WhosUp(user_id=ctx.author.id,expire_at=expire_at)
            self.db.add(myStatus)
        else:
            myStatus = query2.one()
            myStatus.expire_at = expire_at
        self.db.commit()

        # get common game they have
        query1 = self.db.query(WhosUp).filter(WhosUp.expire_at > now)
        players_waiting = query1.all()
        all_users_games_list = []
        if query1.count() > 1:
            for player in players_waiting:
                player_games_list = self.db.query(Games.name).join(UserGames).filter(UserGames.user_id == player.user_id,Games.multiplayer==True).all()
                all_games_list = []
                for game in player_games_list:
                    all_games_list.append(game.name)
                all_users_games_list.append(all_games_list)
            commons_games = set(all_users_games_list[0]).intersection(*all_users_games_list[:1])
            listing = list(commons_games)
            final_games_list = '\n- '.join(listing[:20])
            header += "\nI Suggest you one of this multiplayer games you have in common:\n- {}".format(final_games_list)

            await interntools.paginate(ctx, listing, header=header, footer=footer)
        else:
            await ctx.channel.send(f"{header}{nl}{footer}")

    @commands.command()
    @commands.guild_only()
    async def lfg(self, ctx, *, param: str):
        """ (ex: lfg valheim 10)say you're looking <nb>(default 2) players for <game name>"""
        match = re.match(r"([\D|\s]+)(\d*)", param, re.I)
        if match:
            game, nb_players = match.groups()
        embed = discord.Embed(title=f'{ctx.author.display_name} is searching for a group!')
        embed.add_field(name='Game', value=f'{game}')
        embed.add_field(name='Nb Players wanted', value=f'{nb_players or 2}')
        embed.set_footer(text='react with 👍 if you are interested to join')
        await ctx.message.delete()
        msg = await ctx.channel.send(embed=embed)

    @commands.command()
    async def about(ctx):
        """ display informations about this bot """
        embed = discord.Embed(title=f'About games-matcher')
        desc = "games-matcher is an [open source](https://github.com/dbuteau/games-matcher) discord bot to help gamers found other gamers to play with on their common games."
        desc += "\nYou can thank me by [paying me a beer](https://paypal.me/DanielButeau)"
        embed.description = desc
        embed.add_field(name='version', value=f'{version}')
        embed.add_field(name='Report a bug', value='[here](https://github.com/dbuteau/games-matcher/issues/new)')
        await ctx.channel.send(embed=embed)