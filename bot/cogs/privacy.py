import logging
from textwrap import dedent
import discord
from discord.ext import commands
from libs.models import Users, Games, UserGames, Servers, Base, WhosUp

class Privacy(commands.Cog):
    """ Control how bot interact with your privacy """
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.group(pass_context=True, cog_name='Privacy')
    async def privacy(self, ctx):
        """ `help privacy` for more infos """
        nl = "\n"
        if isinstance(ctx.channel, discord.channel.DMChannel):
            if ctx.invoked_subcommand is None:
                await ctx.author.send(f'Invalid sub command passed...{nl}See `{self.bot.command_prefix}help privacy` for more info')
        else:
            await ctx.message.delete()
            await ctx.author.send('You should send privacy commands in private message')

    @privacy.command()
    async def status(self, ctx):
        """ display what the bot know about you """
        query = self.db.query(Users).filter(Users.user_id == ctx.author.id)
        if query.count() == 0:
            oUser = Users(user_id=ctx.author.id)
            self.db.add(oUser)
            self.db.commit()
            self.db.refresh(oUser)
        else:
            oUser = query.one()
            if oUser.disallow_globally:
                status = "disallowed"
            else:
                status = "allowed"
            if oUser.disallow_users:
                black_list = "\n".join(query.disallow_users.split(','))
            else:
                black_list = "nobody"

            query = self.db.query(UserGames).filter(UserGames.user_id == ctx.author.id)
            embed = discord.Embed(title="What we know about you")
            embed.add_field(name="Your Discord id:", value=ctx.author.id)
            embed.add_field(name="Your activity collect is:", value=f"{status}")
            embed.add_field(name="Your blacklist contain:", value=f"{black_list}")
            embed.add_field(name='Number of your multiplayer owned Games:', value=f"{query.count()}")
            footer = dedent(f"""
            if you own more than 0 games while you disallowed to collect your activity, it's surely because the data were collected before you disallowed it.
            you can erase all your owned game by typing `{self.bot.command_prefix}privacy delete` command""")
            embed.set_footer(text=footer)
            await ctx.author.send(embed=embed)

    @privacy.command()
    async def disallow(self, ctx):
        """ the bot stop to listen your activity """
        query = self.db.query(Users).filter(Users.user_id == ctx.author.id)
        oUser = query.one()
        if oUser.disallow_globally:
            oUser.disallow_globally = False
            await ctx.channel.send('Your Activity collect is now reactivated')
        else:
            oUser.disallow_globally = True
            await ctx.channel.send('Your Activity collect is now disallowed')
        self.db.commit()

    @privacy.command()
    async def block(self, ctx, member: discord.Member = None):
        oUser = self.db.query(Users).filter(Users.user_id == ctx.author.id).one()
        oUser.disallow_users.append(member.id)
        self.db.commit()

    @privacy.command()
    async def unblock(self, ctx, member: discord.Member = None):
        oUser = self.db.query(Users).filter(Users.user_id == ctx.author.id).one()
        oUser.disallow_users.remove(member.id)
        self.db.commit()

    @privacy.command()
    async def delete(self, ctx):
        """ delete all data we know about you """
        self.db.query(UserGames).filter(UserGames.user_id == ctx.author.id).delete()
        self.db.query(Users).filter(Users.user_id == ctx.author.id).delete()
        self.db.commit()
        await ctx.channel.send('Done! Everything is wiped!')