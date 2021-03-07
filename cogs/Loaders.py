from discord.ext import commands
from discord.ext.commands import has_permissions
import os

class Loaders(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def parse_args(args):
        if not args:
            return ''
        if not args.endswith('.py'):
            args += '.py'
        return args

    async def for_each_cog(self, func, args=None):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and (args is None or args == filename):
                try:
                    if 'unload' in func:
                        self.client.unload_extension('cogs.{}'.format(filename[:-3]))
                except Exception as e:
                    print(filename, e)
                try:
                    if 'load' in func:
                        self.client.load_extension('cogs.{}'.format(filename[:-3]))
                except Exception as e:
                    print(filename, e)

    @commands.command()
    @has_permissions(administrator=True)
    async def load(self, ctx, args):
        args = await self.parse_args(args)
        if not args:
            return
        await self.for_each_cog(['load'], args)
        print('Loaded {}'.format(args))

    @commands.command()
    @has_permissions(administrator=True)
    async def unload(self, ctx, args):
        args = await self.parse_args(args)
        if not args:
            return
        await self.for_each_cog(['unload'], args)
        print('Unloaded {}'.format(args))

    @commands.command()
    @has_permissions(administrator=True)
    async def reload(self, ctx, args):
        args = await self.parse_args(args)
        if not args:
            return
        await self.for_each_cog(['unload', 'load'], args)
        print('Reloaded {}'.format(args))

    @commands.command()
    @has_permissions(administrator=True)
    async def reloadAll(self, ctx):
        await self.for_each_cog(['unload', 'load'])

    @commands.command()
    @has_permissions(administrator=True)
    async def loadAll(self, ctx):
        await self.for_each_cog(['load'])

    @commands.command()
    @has_permissions(administrator=True)
    async def unloadAll(self, ctx):
        await self.for_each_cog(['unload'])


def setup(client):
    client.add_cog(Loaders(client))
