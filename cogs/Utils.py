from discord.ext import commands
from discord.ext.commands import CommandNotFound, has_permissions
from Player import Player

class Utils(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.confirm = None

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        raise error

    @commands.Cog.listener()
    async def on_disconnect(self):
        await self.client.log("Disconnected")

    @commands.Cog.listener()
    async def on_connected(self):
        await self.client.log("Connected")

    @commands.command()
    @has_permissions(administrator=True)
    async def update_region_in_db(self, ctx):
        for role in self.client.RegionRoles:
            for member in self.client.RegionRoles[role].members:
                await self.client.usefulCogs['DB'].set_region_platform("region", member.id, role)

    @commands.command()
    @has_permissions(administrator=True)
    async def update_platform_in_db(self, ctx):
        for role in self.client.PlatformRoles:
            for member in self.client.PlatformRoles[role].members:
                await self.client.usefulCogs['DB'].set_region_platform("platform", member.id, role)

    @commands.command()
    @has_permissions(administrator=True, manage_messages=True)
    async def clear(self, ctx):
        try:
            await ctx.channel.purge(limit=100)
        except Exception as e:
            await self.client.log(e)

    @commands.command()
    @has_permissions(administrator=True, manage_messages=True)
    async def delete(self, ctx):
        toDelete = int(ctx.message.content.split()[1])
        async for msg in ctx.channel.history(limit=toDelete+1):
            await msg.delete()

    @commands.command()
    @has_permissions(administrator=True)
    async def reset_leaderboard(self, ctx):
        self.confirm = await ctx.send("Are you sure you want to reset the leaderboards?")
        await self.confirm.add_reaction(self.client.usefulBasicEmotes['yes'])
        await self.confirm.add_reaction(self.client.usefulBasicEmotes['no'])

    async def confirm_reset(self, action, ctx):
        await self.confirm.delete()
        self.confirm = None
        if action:
            await self.client.usefulCogs['AdminDB'].reset_leaders(ctx)
            return
        else:
            return

    @commands.Cog.listener()
    async def on_reaction_add(self, react, user):
        if user.bot:
            return None
        if not self.confirm or react.message.id != self.confirm.id:
            return None
        if react.emoji != self.client.usefulBasicEmotes['yes'] and react.emoji != self.client.usefulBasicEmotes['no']:
            return None

        if react.emoji == self.client.usefulBasicEmotes['yes']:
            await self.confirm_reset(True, react.message)
        if react.emoji == self.client.usefulBasicEmotes['no']:
            await self.confirm_reset(False, react.message)

    @commands.command()
    @has_permissions(administrator=True)
    async def remove_elo(self, ctx, user, elo):
        try:
            db_user = await self.client.usefulCogs['DB'].get_user(user)
        except Exception as e:
            await self.client.log(e)
            await ctx.channel.send(f"Error updating user. Check <#779488043412226058> for more")
        else:
            done = await self.client.usefulCogs['DB'].lose(user, db_user['elo']-int(elo), fix=True)
            if done == False:
                await ctx.channel.send(f"Error updating user. Check <#779488043412226058> for more")
            elif done == True:
                await ctx.channel.send(f"Successfully removed {elo} elo from <@{user}>")

    @commands.command()
    @has_permissions(administrator=True)
    async def add_elo(self, ctx, user, elo):
        try:
            db_user = await self.client.usefulCogs['DB'].get_user(user)
        except Exception as e:
            await self.client.log(e)
            await ctx.channel.send(f"Error updating user. Check <#779488043412226058> for more")
        else:
            done = await self.client.usefulCogs['DB'].wins(user, db_user['elo']+int(elo), fix=True)
            if done == False:
                await ctx.channel.send(f"Error updating user. Check <#779488043412226058> for more")
            elif done == True:
                await ctx.channel.send(f"Successfully added {elo} elo to <@{user}>")

    @commands.command()
    @has_permissions(administrator=True)
    async def show_user(self, ctx, user):
        await ctx.send(f"```{self.client.usefulCogs['AdminDB'].display_db_user(user)}```")

    @commands.command()
    @has_permissions(administrator=True)
    async def judge(self, ctx, winner, loser):
        winner = self.client.get_user(int(winner))
        loser  = self.client.get_user(int(loser))
        await self.client.log('winner: ',winner, 'loser: ', loser)
        await Player(self.client, winner).wins(Player(self.client, loser), ctx.channel)

def setup(client):
    client.add_cog(Utils(client))
