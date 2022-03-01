import os
import sys
import logging
import textwrap
import asyncio
from datetime import (
    datetime
)
import re
import discord
from discord.channel import VoiceChannel
from discord.ext import commands
from libs.interntools import interntools
from libs.models import (
    Games,
    UserGames,
    WhosUp
)
from sqlalchemy import (
    func,
    desc
)


class Commands(commands.Cog, name='Channel commands'):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.logger = logging.getLogger('discord')

    @commands.command()
    @commands.guild_only()
    async def top(self, ctx, Number=10):
        """ number : Show Top {number}(default 10) games owned by members. """
        try:
            members = ctx.guild.members
            members_id = []
            for member in members:
                members_id.append(member.id)
            query = self.db.query(
                Games.name,
                func.count(UserGames.game_id).label("Nb"),
                Games.release_date)\
                .group_by(UserGames.game_id)\
                .filter(
                    Games.game_id == UserGames.game_id,
                    Games.multiplayer == True,
                    UserGames.user_id.in_((members_id))
                )\
                .order_by(desc('Nb'), desc('release_date')) \
                .limit(Number)
            result = []
            for game in query.all():
                result.append(f'{game.name} ({game.Nb})')
            if query.count() > 0:
                header = f'Top {Number} games with most players:'
                await interntools.paginate(ctx, result, header=header)
            else:
                ctx.channel.send('No Games found')
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception from err

    @commands.command()
    @commands.guild_only()
    async def match(self, ctx, member: discord.Member):
        """ Find commons game between you and @user 
            example: match @morkit84566
        """
        try:
            logging.info(
                f'found common games between {ctx.author.id} and {member.id}')
            """Found games in common with <member> ordered by last activity"""
            query_result = self.db.query(Games).join(UserGames)\
                .filter(
                    Games.game_id == UserGames.game_id,
                    UserGames.user_id == ctx.author.id)\
                .order_by(desc(Games.release_date)).all()

            your_games = []
            for game in query_result:
                your_games.append(game.name)

            query_result = self.db.query(Games).join(UserGames)\
                .filter(
                    Games.game_id == UserGames.game_id,
                    UserGames.user_id == member.id)\
                .order_by(desc(Games.release_date)).all()

            his_games = []
            for game in query_result:
                his_games.append(game.name)
            logging.info(f'your_games: {your_games}, his_games: {his_games}')

            commons_games = list(set(your_games).intersection(his_games))
            logging.info(f'common games: {commons_games}')

            if len(commons_games) > 0:
                header = f'{member.display_name} and you have\
                     {len(commons_games)} games in common:'
                await interntools.paginate(ctx, commons_games, header=header)
            else:
                await ctx.channel.send('No games in common found')
        except Exception as err:
            logging.error(f'Match command raised an exception; {err}')

    @commands.command()
    @commands.guild_only()
    async def find(self, ctx, *, game_name: str):
        """ find members which own the 'game name' 
            example: WOG "Total Warhammer III"
        """
        try:
            self.logger.debug('command find called')
            member_list = []
            embed = discord.Embed(title=f'Search Members owning "{game_name}"')
            search = game_name.lower()
            query = self.db.query(Games.name)\
                    .filter(Games.name.like(search))
            nbresult = query.count()
            self.logger.debug(f'found {nbresult}({type(nbresult)}) games for "{search}"')

            if nbresult == 1:
                users = self.db.query(UserGames.user_id).join(Games).filter(Games.name.like(search)).all()
                for user in users:
                    member = discord.utils.find(lambda m: m.id == user.user_id, ctx.guild.members)
                    if member:
                        member_list.append(member.display_name)
                self.logger.debug(f'found {len(users)} members on total {len(member_list)}')
                if len(member_list) > 0:
                    embed.add_field(name='Result', value='\n'.join(member_list))
                else:
                    embed.add_field(name="Result",value='Sorry found no one on this server owning this game')
                await ctx.channel.send(embed=embed)
            elif nbresult > 1:
                embed.description = "Please be more specific your term returned multiple results."
                if nbresult <= 10:
                    embed.add_field(name='Choices',value='\n'.join([r for r, in query.all()]))
                    await ctx.channel.send(embed=embed)
                else:
                    await interntools.paginate(ctx, [r for r, in query.all()], header=embed.description)
            else:
                embed.add_field(
                    name="Result",
                    value='Sorry found no game with this name, try with "%" char as wildcard if you are not sure of the name')
                await ctx.channel.send(embed=embed)
                
        except commands.NoPrivateMessage:
            await ctx.author.send(
                "This command need to be send in guild channel only,\
                 not in private message")
            pass
        except Exception as err:
            self.logger.error(f'find command raised an exception; {err}')

    @commands.command()
    @commands.guild_only()
    async def up(self, ctx, time=30):
        """ Signal than for X next minutes you'r free for game session,
            example: up 120
        """
        header = f'{ctx.author.name} is ready to play'
        footer = f"*Say you want to play too typing `{ctx.prefix}up`*"
        nl = '\n'

        now = datetime.datetime.now()
        query1 = self.db.query(WhosUp).filter(WhosUp.expire_at > now)
        # get list of other players up too
        if query1.count() > 0:
            players_waiting = query1.all()
            players_list = []
            for player in players_waiting:
                if player.user_id != ctx.author.id:
                    member = discord.utils.find(
                        lambda m: m.id == player.user_id, ctx.guild.members)
                    players_list.append(member.display_name)
            if len(players_list) > 0:
                header += f" like {len(players_list)} others"
            else:
                header += ' but is alone :sob:'
        # add the player to the WhosUp list
        query2 = self.db.query(WhosUp)\
                     .filter(WhosUp.user_id == ctx.author.id)
        delta = datetime.timedelta(minutes=int(time))
        expire_at = datetime.datetime.now() + delta
        if query2.count() == 0:
            myStatus = WhosUp(user_id=ctx.author.id, expire_at=expire_at)
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
                player_games_list = self.db.query(Games.name).join(UserGames)\
                    .filter(
                        UserGames.user_id == player.user_id,
                        Games.multiplayer == True).all()
                all_games_list = []
                for game in player_games_list:
                    all_games_list.append(game.name)
                all_users_games_list.append(all_games_list)
            commons_games = \
                set(all_users_games_list[0])\
                .intersection(*all_users_games_list[:1])
            listing = list(commons_games)
            final_games_list = '\n- '.join(listing[:20])
            header += "\nI Suggest you one of this multiplayer games "\
                      "you have in common:\n- {}".format(final_games_list)

            await interntools.paginate(
                ctx, listing, header=header, footer=footer)
        else:
            await ctx.channel.send(
                f"{header}{nl}{footer}",
                delete_after=(time*60)
            )

    @commands.command()
    @commands.guild_only()
    async def GPN(self,ctx):
        # todo
        """ Games Played Now : currently played games list on the guild server """
        try:
            gamesList = {}
            for user in ctx.guild.members:
                if user.status == discord.Status.online and user.activity.type == 'playing':
                    gamesList[user.activity.name] = (gamesList[user.activity.name] or 0) + 1
            embedModel = discord.Embed(
                title='Members are currently playing to')
            for game, player in gamesList:
                embedModel.add_field(game,player,True)
            else:
                embedModel.add_field('Nothing, absolutly nothing','')
            await ctx.channel.send(embed=embed, delete_after=(30*60))
        except Exception as err:
            self.logger.error(f'lfg command raised an exception; {err}')

    @commands.command()
    @commands.guild_only()
    async def lfg(self, ctx, *, params: str):
        """ Lean For Group of X persons (offer expire after 30mn)
            Example: lfg total war III 4
            When nb players have reacted to the message it automaticly create voice channel with member in it
        """
        def check(reaction: discord.Reaction, user, remove=False):
            try: 
                nonlocal userUpList

                if str(reaction.emoji) == '👍': 
                    if remove:
                        userUpList.remove(user)
                    else:
                        userUpList.append(user)
                if str(reaction.emoji) == '🏁' and user == ctx.author:
                    asyncio.create_task(moveToVoiceChannel(chanName=f'{user.display_name}-{game}', usersList=userUpList))
                    asyncio.create_task(lfgmsg.delete())
                    return
                if str(reaction.emoji) == '❌' and user == ctx.author:
                    asyncio.create_task(lfgmsg.delete())
                    return

                rn = "\n"
                if len(userUpList) >= nb_players:
                    asyncio.create_task(moveToVoiceChannel(chanName=f'{user.display_name}-{game}', usersList=userUpList))
                    asyncio.create_task(lfgmsg.delete())
                else:
                    embed.set_field_at(messageField1, name='Nb Players wanted', value=f'{len(userUpList)}/{nb_players}', inline=True)
                    embed.set_field_at(messageField2, name='Players in group', value=f'{rn.jpoin(userUpList)}', inline=False)
                    asyncio.create_task(update_embed(embed))
                return
            except Exception as err:
                self.logger.error(f'lfg command raised an exception at line {sys.exc_info()[-1].tb_lineno}; {err}')

        async def moveToVoiceChannel(chanName, usersList):
            try:
                # create the voice channel
                overwrites = {
                    ctx.message.author: discord.PermissionOverwrite(connect=True, mute_members=True, move_members=True,
                                                        manage_channels=True)
                }
                for user in usersList:
                    await user.move_to(f'{chanName}', overwrites=overwrites, user_limit=nb_players, reason='bot found a group for playing')
            except discord.Forbidden:
                await ctx.channel.send("Sorry i don't have permissions to create voice channel, you have to create yourself or use existing one")
            except Exception as err:
                self.logger.error(f'lfg command raised an exception at line {sys.exc_info()[-1].tb_lineno}; {err}')

        async def update_embed(embed):
            await lfgmsg.edit(embed=embed)

        try:
            game, nb_players = re.match(r"(?:\")*([\w|\s]+)(?:\")* (\d*)", params, re.I).groups()
            nb_players = int(nb_players)

            embedModel = discord.Embed(
                title=f'{ctx.author.display_name} is searching for a group!',
                color=0xff0000)
            embedModel.add_field(name='Game', value=f'{game}', inline=True)
            footer = """
            react with 👍 if you are interested to join.
            When the number of players wanted is reached a voice channel will be created and persons whom reacted automaticly join the channel.
            For lfg author:
            - 🏁 reaction skip the wait and invite people in the list to voice channel
            - ❌ reaction cancel and delete the lfg
            """
            embedModel.set_footer(text=textwrap.dedent(footer))

            embed = embedModel
            messageField1 = embed.add_field(name='Nb Players wanted', value=f'1/{nb_players}', inline=True)
            messageField2 = embed.add_field(name='Players in group:', value=f'{ctx.author.display_name}', inline=False)
            await ctx.message.delete()

            lfgmsg = await ctx.channel.send(embed=embed, delete_after=(30*60))

            userUpList = []
            userUpList.append(ctx.author)

            def remove(reaction: discord.Reaction, user):
                check(reaction, user, remove=True)

            # Listening for reaction changes on the message
            await self.bot.wait_for(event='reaction_add', timeout=(30*60), check=check)
            await self.bot.wait_for('raw_reaction_remove', timeout=(30*60), check=remove)
        except asyncio.TimeoutError:
            await lfgmsg.delete()
        except Exception as err:
            self.logger.error(f'lfg command raised an exception at line {sys.exc_info()[-1].tb_lineno}; {err}')


class Both(commands.Cog, name='Misc.'):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.command()
    async def about(self, ctx):
        """ display informations about this bot """
        fo = open("version", "r")
        version = fo.readline()
        embed = discord.Embed(title='About games-matcher')
        desc = \
            "games-matcher is an "\
            "[open source](https://github.com/dbuteau/games-matcher)"\
            " discord bot to help gamers found other gamers"\
            " to play with on their common games."
        desc += \
            "\nYou can thank me by "\
            "[paying me a beer](https://paypal.me/DanielButeau)"
        desc += \
            "\nYou can join [this channel](https://discord.gg/4bhFFnCatf) if you want to help testing"\
            " the beta version of this bot"
        embed.description = desc
        embed.add_field(name='version', value=f'{version}')
        embed.add_field(
            name='Report a bug',
            value='[here](https://github.com/dbuteau/games-matcher/issues/new)'
        )
        await ctx.channel.send(embed=embed)
