import os
from discord.ext import commands
from const import *


class DarwinBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        # Now self has client

        self.db = None
        # Initializing constants
        self.server = None
        self.usefulChannels = {}
        self.challRooms = {}
        self.usefulRoles = {}
        self.RankRoles = {}
        self.RegionRoles = {}
        self.PlatformRoles = {}
        self.BracketRoles = {}
        self.usefulCustomEmotes = {}
        self.usefulBasicEmotes = {}
        self.usefulCogs = {}
        self.supporterRoles = {}
        self.platformColours = {}
        self.platformImages = {}
        self.DuelRequests = []
        self.Rooms = []
        self.Active = []

        # Non - constant variable initialization

        # Loading the server, channels, roles...
        for filename in os.listdir('./init'):
            if filename.endswith('.py'):
                self.load_extension('init.{}'.format(filename[:-3]))

        # Loading cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                self.load_extension('cogs.{}'.format(filename[:-3]))

        for (var, cog) in UsefulCogs:
            self.usefulCogs[var] = self.get_cog(cog)

    async def log(self, *args):
        msg = ' '.join([str(x) for x in args])
        if self.usefulChannels['logs']:
            await self.usefulChannels['logs'].send("```{}```".format(msg))
        print(msg, flush=True)

    class MissingSomething(Exception):
        def __init__(self, *args):
            if args:
                self.message = args[0]
            else:
                self.message = None

        def __str__(self):
            if self.message:
                return 'MissingSomething, {0} '.format(self.message)
            else:
                return 'MissingSomething has been raised'