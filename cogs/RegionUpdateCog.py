import discord
from discord.ext import commands


class RegionUpdateCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        for role in self.client.RegionRoles:
            wasAttributed = self.client.RegionRoles[role] in before.roles
            isAttributed = self.client.RegionRoles[role] in after.roles
            if not wasAttributed and isAttributed:
                await self.client.usefulCogs['DB'].set_region_platform("region", after.id, role)
            elif wasAttributed and not isAttributed:
                await self.client.usefulCogs['DB'].remove_region_platform("region", after.id, role)
        for role in self.client.PlatformRoles:
            wasAttributed = self.client.PlatformRoles[role] in before.roles
            isAttributed = self.client.PlatformRoles[role] in after.roles
            if not wasAttributed and isAttributed:
                await self.client.usefulCogs['DB'].set_region_platform("platform", after.id, role)
            elif wasAttributed and not isAttributed:
                await self.client.usefulCogs['DB'].remove_region_platform("platform", after.id, role)


def setup(client):
    client.add_cog(RegionUpdateCog(client))
