import discord
from discord.ext import commands
import random

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
        if ctx.message.channel in self.client.challRooms.values():
            return
        try:
            user = ctx.message.mentions[0]
        except:
            user = ctx.author
        db_user = await self.client.usefulCogs['DB'].get_user(user.id)
        platform = db_user['platform']
        platformColour = self.client.platformColours[platform]
        platformImage = self.client.platformImages[platform]
        
        rRank = await self.client.usefulCogs['DB'].get_user_rank(user_id=user.id, platform=platform, region=db_user['region'])
        if db_user['victory']+db_user['defeat'] < 10:
            await ctx.send(f"You must play 10 games to receive your first rank. {db_user['victory']+db_user['defeat']}/10 games played")
            return
        gRank = await self.client.usefulCogs['DB'].get_user_rank(user_id=user.id)

        embed = discord.Embed(
            color = discord.Colour(platformColour),
            title = f"{user.display_name}",
        )
        embed.add_field(name="Region", value= db_user['region'], inline=False)
        embed.add_field(name="Elo", value= db_user['elo'], inline=False)
        embed.add_field(name="Qualifying Rank", value= int(rRank['rank']), inline=False)
        embed.add_field(name="Global Rank", value= int(gRank['rank']), inline=False)
        embed.add_field(name="Victories", value= db_user['victory'], inline=True)
        embed.add_field(name="Defeats", value= db_user['defeat'], inline=True)
        
        embed.set_author(name="Player Card", icon_url = platformImage)
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def flip(self, ctx):
        if ctx.channel in self.client.usefulChannels.values():
            flip = random.randint(0,1)
            if flip == 1: 
                await ctx.send('Heads')
            else: 
                await ctx.send('Tails')
        else:
            await ctx.message.delete()

    @commands.command()
    async def rules(self, ctx):
        await ctx.send("""**__Suggested Rules__**
```1. 10 Wood
2. No Items
3. No Traps
4. No Deer
5. Campfire in Middle```""")

    @commands.command()
    async def leaderboard(self, ctx):
        await ctx.send("https://www.darwin1v1league.com/leaderboard")

    @commands.command()
    async def qual(self, ctx):
        if ctx.message.channel in self.client.challRooms.values():
            return

        db_user = await self.client.usefulCogs['DB'].get_user(ctx.author.id)
        platform = db_user['platform']
        platformColour = self.client.platformColours[platform]
        platformImage = self.client.platformImages[platform]
        region = db_user['region']

        qualRes = await self.client.usefulCogs['DB'].get_qual(platform, region)
        if not qualRes:
            await ctx.send('No Qualified Players')
            return
        players = [list(user.values())[0] for user in qualRes]
        ranked = ''
        for player in players:
            ranked = ranked + f'\n{players.index(player)+1}. {player}'

        embed = discord.Embed(
            color = discord.Colour(platformColour),
            description = ranked,
        )
        embed.set_author(name=f"Qualifying {region} Players", icon_url = platformImage)
        await ctx.send(embed=embed)



def setup(client):
    client.add_cog(UserCommands(client))