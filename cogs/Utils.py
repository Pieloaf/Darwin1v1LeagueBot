from discord.ext import commands
from discord.ext.commands import CommandNotFound, has_permissions
from Player import Player
import os
from discord import File
import numpy as np

class Utils(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.confirm = None
        self.season = None

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
    async def reset_leaderboard(self, ctx, season):
        self.confirm = [season, await ctx.send("Are you sure you want to reset the leaderboards?")]
        await self.confirm[1].add_reaction(self.client.usefulBasicEmotes['yes'])
        await self.confirm[1].add_reaction(self.client.usefulBasicEmotes['no'])

    async def confirm_reset(self, action, ctx):
        season = self.confirm[0]
        await self.confirm[1].delete()
        self.confirm = None
        if action:
            await self.client.usefulCogs['AdminDB'].reset_leaders(ctx, season)
            await self.reset_ranks(ctx)
            return
        else:
            return

    @commands.Cog.listener()
    async def on_reaction_add(self, react, user):
        if user.bot:
            return None
        if not self.confirm or react.message.id != self.confirm[1].id:
            return None
        if react.emoji != self.client.usefulBasicEmotes['yes'] and react.emoji != self.client.usefulBasicEmotes['no']:
            return None

        if react.emoji == self.client.usefulBasicEmotes['yes']:
            await self.confirm_reset(True, react.message)
        elif react.emoji == self.client.usefulBasicEmotes['no']:
            await self.confirm_reset(False, react.message)

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

    @commands.command()
    @has_permissions(administrator=True)
    async def challenge_zone(self, ctx, platform):
        await ctx.send(f"```Welcome to {platform} Challenge Zone: @1v1 to challenge anyone or @ a specific user to send a challenge.```")

    @commands.command()
    @has_permissions(administrator=True)
    async def reset_ranks(self, ctx):
        await ctx.channel.send("Resetting ranks...")
        for role in list(self.client.RankRoles.values()):
            for member in role.members:
                await member.remove_roles(role)
                await member.add_roles(self.client.usefulRoles['Unranked'])
        await ctx.channel.send(f"{ctx.author.mention} rank reset done")
    
    @commands.command()
    @has_permissions(administrator=True)
    async def revert(self, ctx, *args):
        game_ids = []
        user = None
        limit = ignore = 0
        try:
            game_ids = [int(arg) for arg in args]
        except ValueError:
            for arg in args:
                try:
                    if arg == '-u':
                        user = int(args[args.index(arg)+1])
                    elif arg == '-n':
                        limit = int(args[args.index(arg)+1])
                    elif arg == '-i':
                        ignore = int(args[args.index(arg)+1])
                except ValueError:
                    await ctx.send('Error Invalid Syntax')
                    return
            toLim = limit+ignore if limit != 0 else 0
            try:
                game_ids = [int(game['game_id']) for game in await self.client.usefulCogs['DB'].games_to_revert(int(user), toLim)]
            except TypeError:
                await ctx.send("Somthine went wrong :thinking:")
                return
        game_ids = game_ids[ignore:]
        for game_id  in game_ids:
            game = await self.client.usefulCogs['DB'].get_game(game_id)

            await self.client.usefulCogs['DB'].delete_game(game_id)
            win = await self.client.usefulCogs['DB'].wins(game['loser'], game['elo_loss'], revert=True)
            lose = await self.client.usefulCogs['DB'].lose(game['winner'], game['elo_gain'], revert=True)
            if win == False or lose == False:
                await ctx.send("Error on reverting game. Check <#779488043412226058> for more")
            else:
                await ctx.send(f"Successfully reverted game https://discord.com/channels/779485288996012052/794640641157234698/{str(game_id)}")

    @commands.command()
    @has_permissions(administrator=True)
    async def patches(self, ctx, season=''):
        patch_dir = '/var/www/vhosts/darwin1v1league.com/httpdocs/patch_notes/season-{}.json'
        try:
            int(season)
        except ValueError:
            await ctx.send('Please specify a season for the patch notes')
            return

        try:
            await ctx.message.attachments[0].save(f'season-{season}.json')
        except IndexError as e:
            if os.path.isfile(patch_dir.format(season)):
                await ctx.send(content=f'Latest Season {season} Patch Notes:', file=File(patch_dir.format(season)))
                if os.path.isfile(patch_dir.format(f'{season}-backup')):
                    await ctx.send(content=f'Previous Season {season} Patch Notes:', file=File(patch_dir.format(f'{season}-backup')))
            else:
                await ctx.send(f'No previous patch notes for season {season}')
            return

        if os.path.isfile(patch_dir.format(season)):
            os.rename(patch_dir.format(season), patch_dir.format(f'{season}-backup'))
        os.rename(f'./season-{season}.json', (patch_dir.format(season)))
        await ctx.send(f'Successfully Updated Patch Notes for Season {season}')


def setup(client):
    client.add_cog(Utils(client))
