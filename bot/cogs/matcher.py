import datetime
import logging
import discord
from discord.ext import commands
from libs.models import Users, Games, UserGames, WhosUp
from libs.interntools import interntools
from sqlalchemy import desc

class Functions(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.command()
    @commands.guild_only()
    async def up(self, ctx, time=30):
        """ Signal you are up for game session, the offer expire in <time> minutes (Not Yet Implemented)"""
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

    @commands.command(hidden=True)
    @commands.guild_only()
    async def match(self, ctx, member: discord.Member):
        """ Found games in common with <member> ordered by last activity """
        query_result1 = self.db.query(Games.name).join(UserGames).filter(Games.game_id == UserGames.game_id, UserGames.user_id == ctx.author.id).all()
        query_result2 = self.db.query(Games.name).join(UserGames).filter(Games.game_id == UserGames.game_id, UserGames.user_id == member.id).all()
        your_games = []
        for game in query_result1:
            logging.info(game.name)
            your_games.append(game.name)
        his_games = []
        for game in query_result2:
            his_games.append(game.name)
        commons_games = list(set(your_games).intersection(his_games))
        logging.info(f'found {len(commons_games)} games in common')
        if len(commons_games) > 0:
            header = '{0} and you have {1} games in common:'.format(member.display_name,len(commons_games))
            await interntools.paginate(ctx, commons_games, header=header)
        else:
            await ctx.channel.send('No games in common found')



    @commands.command()
    @commands.guild_only()
    async def find(self, ctx, game_name):
        """ find members which own the game <game name> """
        try:
            member_list = []
            search = game_name.lower()
            users = self.db.query(UserGames.user_id).join(Games).filter(Games.name==search).all()
            for user in users:
                if not user.user_id == ctx.author.id:
                    member = discord.utils.find(lambda m: m.id == user.user_id, ctx.guild.members)
                    if member:
                        member_list.append(member.display_name)
            if len(member_list) > 0:
                msg = """
                Gamer which own "{game_name.lower()}" {len(member_list)}
                {'\n'.join(member_list)}
                """
                await ctx.author.send(msg)
            else:
                games = self.db.query(Games.name).filter(Games.name.ilike(f'%{game_name[0:4]}%')).limit(4).all()
                alternate_games = []
                for game in games:
                    if game.name != game_name:
                        alternate_games.append(game.name)
                flat_games = ', '.join(alternate_games)
                msg = f"No one on the server own '{game_name}'"
                if len(alternate_games)>0:
                    msg += f", \nwould you mean: {flat_games}"
                await ctx.author.send(msg)
        except commands.NoPrivateMessage :
            await ctx.author.send("This command need to be send in guild channel only, not in private message")
            pass
