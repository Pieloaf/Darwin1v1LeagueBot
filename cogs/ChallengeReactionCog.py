from urllib.parse import urlparse, parse_qs
import discord
from discord.ext import commands
from Room import Room
from Request import Request

from const_messages import CHALL_ME_TITLE, MAX_GAMES


class ChallengeReaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    def is_it_this_request(req, msg, user):
        if user.bot:
            return False
        if msg.id != req['req'].message.id:
            return False
        if user.id != req['req'].defender.id and user.id != req['req'].attacker.id:
            return False
        return True

    def is_it_a_request_msg(self, react, user):
        if user.bot:
            return False
        if react.emoji != self.client.usefulBasicEmotes['yes'] and react.emoji != self.client.usefulBasicEmotes['no']:
            return False
        for channel in self.client.challRooms.values():
            if react.message.channel.id == channel.id:
                return True
            
        return True

    async def max_challenge(self, author, user, reaction):
        count = await self.client.usefulCogs['DB'].game_count(author.id, user.id)
        if count >= 5:
            await reaction.remove(user)
            await user.send(MAX_GAMES)
            return True
        return False

    def get_embed_author(self, message):
        if message.embeds[0].author.name != "Mystery Challenger":
            return discord.utils.get(self.client.server.members, discriminator=message.embeds[0].author.name[-4:], name=message.embeds[0].author.name[:-5])
        
        url = message.embeds[0].author.icon_url
        result = list(parse_qs(qs=url).values())[0]
        return self.client.server.get_member(int(result[0]))


    def get_valid_request(self, react, user):
        ## Checking if it is a 'duel request' message
        for req in self.client.DuelRequests:
            if self.is_it_this_request(req, react.message, user):
                return req
        ## Now checking if it is a 'challenge me' message
        if react.emoji != self.client.usefulBasicEmotes['yes'] and react.emoji != self.client.usefulBasicEmotes['no']:
            return None

        if react.message.embeds and react.message.embeds[0].title == CHALL_ME_TITLE:
            author = self.get_embed_author(react.message)
            if not author:
                return None
            req = Request(react.message, author, user)

            return {'req': req, 'chall_me':True}
        return None

    async def create_room(self, msg, attacker, defender):
        new_room = Room(msg, attacker, defender, self.client)
        await new_room.create()
        self.client.Rooms.append(new_room)

    @commands.Cog.listener()
    async def on_reaction_add(self, react, user):
        if not self.is_it_a_request_msg(react, user):
            return
        request = self.get_valid_request(react, user)
        if not request:
            return
        author = self.get_embed_author(react.message)
        if react.emoji == self.client.usefulBasicEmotes['yes']:
            if author.id == user.id:
                return
            if 'chall_me' in request and await self.max_challenge(author, user, react):
                return
            await self.create_room(request['req'].message, request['req'].attacker, request['req'].defender)
            if request in self.client.DuelRequests:
                self.client.DuelRequests.remove(request)
        elif react.emoji == self.client.usefulBasicEmotes['no']:
            if 'chall_me' in request and author.id != user.id:
                return
            await request['req'].message.delete()
            if not 'chall_me' in request:
                self.client.DuelRequests.remove(request)

def setup(client):
    client.add_cog(ChallengeReaction(client))
