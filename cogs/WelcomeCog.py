import discord
from discord.ext import commands
import json


class WelcomeCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, memeber):
        if memeber.bot:
            return
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(46, 204, 113),
            title="Welcome Challenger!",
            description=
            f'Welcome to the Darwin 1v1 League Discord Server, {memeber.mention}!',
        )
        embed.set_thumbnail(url=str(memeber.avatar_url))
        await self.client.usefulChannels['welcome'].send(embed=embed)


def setup(client):
    client.add_cog(WelcomeCog(client))