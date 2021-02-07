import discord
from discord.ext import commands
from libs.models import Users, Games, UserGames, Servers, Base, WhosUp

class Privacy(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    @commands.command()
    async def status(self, ctx):
        """ display privacy status for the user """
        MSG_STATUS = """
            You {} games-matcher to collect data from your activity\n
            Your blacklist contain:\n
                {}
            """
        query = self.db.query(Users).get(ctx.author.id).one()
        if query.disallow_globally:
            status = "allowed"
        else:
            status = "disallowed"
        if query.disallow_users:
            black_list = "\n".join(query.disallow_users.split(','))
        else:
            black_list = "nobody"
        await ctx.author.send(MSG_STATUS.format(status, black_list))

    @commands.command()
    async def disallow(self, ctx):
        """ the bot stop to listen your activity """
        oUser = self.db.query(Users).get(ctx.author.id).one()
        if oUser.disallow_globally:
            oUser.disallow_globally = False
            await ctx.channel.send('Your Activity collect is now reactivated')
        else:
            oUser.disallow_globally = True
            await ctx.channel.send('Your Activity collect is now disallowed')
        db.commit()

    @commands.command()
    async def block(self, ctx, member: discord.Member = None):
        pass

    @commands.command()
    async def unblock(self, ctx, member: discord.Member = None):
        pass

    @commands.command()
    async def delete(self, ctx):
        """ delete all data we know about you """
        self.db.query(UserGames).filter(UserGames.user_id == ctx.author.id).delete()
        self.db.query(Users).filter(Users.user_id == ctx.author.id).delete()
        self.db.commit()
        await ctx.channel.send('Done! Everything is wiped!')
