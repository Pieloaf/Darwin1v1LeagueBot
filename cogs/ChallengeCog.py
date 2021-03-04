import discord
from discord.ext import commands
from const_messages import *
from Request import Request
from datetime import datetime
from Room import Room
from urllib.parse import urlparse, parse_qs

class ChallengeCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    def get_member_platform(self, author):
        platforms = ''
        possible_platform_roles = ['PC', 'Xbox', 'PS4']
        for role in author.roles:
            if role.name in possible_platform_roles:
                platforms += role.name + '\t'
        if not platforms:
            return ''
        return platforms

    def get_member_region(self, author):
        region = ''
        possible_region_roles = ['EU', 'NA-East']
        for role in author.roles:
            if role.name in possible_region_roles:
                region += role.name + '\t'
        if not region:
            return ''
        return region

    def set_embed_platform_region_footer_author(self, embed, author, mystery):
        if mystery == True:
            embed.set_author(name="Mystery Challenger", icon_url=MYSTERY_ICON_URL.format(author.id))
        else:
            embed.set_author(name=author, icon_url=f'{author.avatar_url}&user_id={author.id}')
        platforms = self.get_member_platform(author)
        if platforms:
            embed.add_field(name='Platform', value=platforms)
        regions = self.get_member_region(author)
        if regions:
            embed.add_field(name='Region', value=regions)
        embed.set_footer(text=DELETED_IN.format(2))
        return embed

    def create_embed_msg(self, author, mention):
        e = discord.Embed(color=discord.Color.dark_orange())
        e.add_field(name='FIGHT', value=DUEL_REQUEST_MSG.format(author.mention, mention.mention))
        e = self.set_embed_platform_region_footer_author(e, author, False)
        return e

    def create_embed_msg_me(self, author):
        e = discord.Embed(color=discord.Color(4397185), title=CHALL_ME_TITLE)
        e.add_field(name='FIGHT', value=DUEL_ME_REQUEST_MSG)
        e = self.set_embed_platform_region_footer_author(e, author, True)
        return e

    async def challenge(self, message):
        if await self.already_challenged(message):
            return
        author = message.author
        content = message.content
        channel = message.channel
        mention = message.mentions[0]
        await message.delete()
        if await self.max_challenge(author, mention):
            return
        e = self.create_embed_msg(author, mention)
        botMsg = await channel.send(embed=e, delete_after=60 * 2)
        await botMsg.add_reaction(self.client.usefulBasicEmotes['yes'])
        await botMsg.add_reaction(self.client.usefulBasicEmotes['no'])
        req = Request(botMsg, author, mention)
        self.client.DuelRequests.append({'req': req, 'time': datetime.now()})

    def get_embed_author(self, message):
        
        url = message.embeds[0].author.icon_url
        result = list(parse_qs(qs=url).values())[-1]
        return self.client.server.get_member(int(result[-1]))

    async def already_challenged(self, message):
        async for msg in message.channel.history(limit=50):
            if msg.embeds and len(msg.embeds):
                author = self.get_embed_author(msg)
                if author.id == message.author.id:
                    await message.delete()
                    await message.author.send(TAKE_A_BREATH)
                    return True
        return False
    
    async def max_challenge(self, author, mention):
        count = await self.client.usefulCogs['DB'].game_count(author.id, mention.id)
        if count >= 5:
            await author.send(MAX_GAMES)
            return True
        return False

    async def create_room(self, msg, attacker, defender):
        new_room = Room(msg, attacker, defender, self.client)
        await new_room.create()
        self.client.Rooms.append(new_room)

    async def create_chall(self, someone_else, someone_else_msg, message):
        await self.create_room(someone_else_msg, someone_else, message.author)
        await message.delete()

    async def chall_me(self, message):
        if await self.already_challenged(message):
            return
        author = message.author
        channel = message.channel
        await message.delete()
        e = self.create_embed_msg_me(author)
        botMsg = await channel.send(embed=e, delete_after=60 * 2)
        await botMsg.add_reaction(self.client.usefulBasicEmotes['yes'])
        await botMsg.add_reaction(self.client.usefulBasicEmotes['no'])

    @staticmethod
    async def chall_yourself(message):
        await message.author.send(content=CHALLENGE_YOURSELF_MESSAGE)
        await message.delete()



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not self.client.challRooms:
            return
        for channel in self.client.challRooms.values():
            if message.channel.id != channel.id and list(self.client.challRooms.values()).index(channel) == len(self.client.challRooms.values())-1:
                return
            elif message.channel.id == channel.id:
                break
        if not message.mentions or len(message.mentions) != 1:
            await message.delete()
            return
        if message.mentions[0].id == self.client.user.id:
            return await self.chall_me(message)
        if message.mentions[0].id == message.author.id:
            return await self.chall_yourself(message)
        await self.challenge(message)



def setup(client):
    client.add_cog(ChallengeCog(client))
