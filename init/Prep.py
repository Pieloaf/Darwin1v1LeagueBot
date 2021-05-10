import discord
from discord.ext import commands
from const import *


class Prep(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def init_server(self):
        server = discord.utils.get(self.client.guilds, id=ServerId)
        if not server:
            raise self.client.MissingSomething("Discord server not found")
        self.client.server = server

    async def init_channels(self):
        for (var, chanName) in UsefulChannelNames:
            channel = discord.utils.get(self.client.server.channels, name=chanName)
            if not channel:
                raise self.client.MissingSomething("{} channel is missing".format(chanName))
            self.client.usefulChannels[var] = channel

    async def init_challRooms(self):
        for (var, chanName) in ChallengeRooms:
            channel = discord.utils.get(self.client.server.channels, name=chanName)
            if not channel:
                raise self.client.MissingSomething("{} channel is missing".format(chanName))
            self.client.challRooms[var] = channel

    async def init_cmdChannels(self):
        for (var, chanName) in CommandsChannels:
            channel = discord.utils.get(self.client.server.channels, name=chanName)
            if not channel:
                raise self.client.MissingSomething("{} channel is missing".format(chanName))
            self.client.cmdChannels[var] = channel

    async def init_roles(self):
        for (var, roleName) in UsefulRoles:
            role = discord.utils.get(self.client.server.roles, name=roleName)
            if not role:
                raise self.client.MissingSomething("{} role is missing".format(roleName))
            self.client.usefulRoles[var] = role

    async def init_region_roles(self):
        for (var, roleName) in RegionRoles:
            role = discord.utils.get(self.client.server.roles, name=roleName)
            if not role:
                raise self.client.MissingSomething("{} role is missing".format(roleName))
            self.client.RegionRoles[var] = role

    async def init_platform_roles(self):
        for (var, roleName) in PlatformRoles:
            role = discord.utils.get(self.client.server.roles, name=roleName)
            if not role:
                raise self.client.MissingSomething("{} role is missing".format(roleName))
            self.client.PlatformRoles[var] = role

    async def init_rank_roles(self):
        for (var, roleName, elo) in RankRoles:
            role = discord.utils.get(self.client.server.roles, name=roleName)
            if not role:
                raise self.client.MissingSomething("{} role is missing".format(roleName))
            self.client.RankRoles[var] = role

    async def init_bracket_roles(self):
        for (var, roleName) in sorted(BracketRoles, key=lambda x: x[1]):
            role = discord.utils.get(self.client.server.roles, name=roleName)
            if not role:
                raise self.client.MissingSomething("{} role is missing".format(roleName))
            self.client.BracketRoles[var] = role

    async def init_custom_emotes(self):
        for (var, emoteName) in UsefulCustomEmotes:
            emote = discord.utils.get(self.client.server.emojis, name=emoteName)
            if not emote:
                raise self.client.MissingSomething("{} emote is missing".format(emoteName))
            self.client.usefulCustomEmotes[var] = emote

    async def init_basic_emotes(self):
        for (var, emote) in UsefulBasicEmotes:
            self.client.usefulBasicEmotes[var] = emote

    async def init_platform_images(self):
        for (var, image) in PlatformImages:
            self.client.platformImages[var] = image

    async def init_platform_colours(self):
        for (var, colour) in PlatformColours:
            self.client.platformColours[var] = colour


    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.init_server()
            await self.init_channels()
            await self.init_challRooms()
            await self.init_cmdChannels()
            await self.init_roles()
            await self.init_region_roles()
            await self.init_platform_roles()
            await self.init_rank_roles()
            await self.init_bracket_roles()
            await self.init_custom_emotes()
            await self.init_basic_emotes()
            await self.init_platform_images()
            await self.init_platform_colours()
        except self.client.MissingSomething as e:
            await self.client.log(e)
            await self.client.log("The bot will shut down, please check the discord server for whatever is missing.")
            exit(84)


def setup(client):
    client.add_cog(Prep(client))
