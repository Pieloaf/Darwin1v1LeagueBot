import discord
from discord.ext import commands


class UserCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Activity(name="Humans fight", type=discord.ActivityType.watching)
        await self.client.change_presence(status=discord.Status.dnd, activity=game)
        await self.client.log('Bot Ready')

    @commands.command()
    async def rank(self, ctx):
        try:
            user = ctx.message.mentions[0]
        except:
            user = ctx.author
        db_user = await self.client.usefulCogs['DB'].get_user(user.id)
        platform = db_user['platform']
        platformColour = self.client.platformColours[platform]
        
        rank = await self.client.usefulCogs['DB'].get_user_rank(platform, user.id)
        if not rank or db_user['victory']+db_user['defeat'] < 10:
            await ctx.send("You must play 10 games to receive your first rank")
            return

        embed = discord.Embed(
            color = discord.Colour(platformColour),
            title = f"{user.display_name}",
        )
        embed.add_field(name=f"Platform", value= platform, inline=True)
        embed.add_field(name=f"Rank", value= int(rank['rank']), inline=True)
        embed.add_field(name=f"Elo", value= db_user['elo'], inline=True)
        embed.add_field(name=f"Victories", value= db_user['victory'], inline=True)
        embed.add_field(name=f"Defeats", value= db_user['defeat'], inline=True)
        
        embed.set_author(name="Player Card", icon_url = 'https://cdn.discordapp.com/avatars/779767593418227735/abd2384d28df211f58550249951dd147.png?size=4096')
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(UserCommands(client))