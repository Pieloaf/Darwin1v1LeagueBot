import asyncio
import inspect
import discord
from time import strftime, gmtime
from Player import Player
from const_messages import \
    CONFLICT_MSG, \
    ADMIT_DEFEAT_MSG, \
    CLAIM_VICTORY_MSG, \
    CLAIM_VICTORY_LOG, \
    START_GAME_TITLE, \
    START_DUEL_MSG, \
    DUEL_RESULTS_MSG, \
    START_DUEL_TITLE


class Room:
    def __init__(self, duel_request_msg, attacker, defender, client):
        self.client = client
        self.duelRequestMsg = duel_request_msg
        self.attacker = attacker
        self.defender = defender
        self.bracket = None
        self.channel = None
        self.result_msg = None
        self.result_reactions = {'a': None, 'd': None}
        self.results = None
        self.winner = None
        self.task = None

    async def clear(self):
        for member in self.bracket.members:
            await member.remove_roles(self.bracket)
        await self.channel.purge()

    def get_winner_and_loser(self):
        if self.winner == 'a':
            return self.attacker, self.defender
        return self.defender, self.attacker

    async def set_winner(self, value):
        if self.winner:
            return
        self.winner = value
        winner, loser = self.get_winner_and_loser()
        await Player(self.client, winner).wins(Player(self.client, loser), self.channel)
        await self.channel.send('```This room will close in 10 seconds...```')
        self.client.loop.create_task(self.call_this_in(self.clear, (), 10))

    def is_this_reaction_for_me(self, react, user):
        if user.id != self.attacker.id and user.id != self.defender.id:
            return False
        if react.message.id != self.result_msg.id:
            return False
        return True

    async def claim_was_right(self, winner):
        await self.set_winner(winner)

    @staticmethod
    async def call_this_in(func, args, time):
        await asyncio.sleep(time)
        if inspect.iscoroutinefunction(func):
            if args:
                return await func(args)
            return await func()
        if args:
            return func(args)
        return func()

    async def claimed_victory(self, letter, who, on_who):
        await self.channel.send(CLAIM_VICTORY_MSG.format(who.name, on_who.name, on_who.mention))
        await self.client.log(CLAIM_VICTORY_LOG.format(who.name, on_who.name, strftime("%Y-%m-%d %H:%M", gmtime())))
        self.task = self.client.loop.create_task(self.call_this_in(self.claim_was_right, letter, 420))

    async def check_results(self):
        if self.task:
            self.task.cancel()
        if self.result_reactions['d'] == self.result_reactions['a']:
            await self.channel.send(CONFLICT_MSG)
        elif self.result_reactions['a'] == 0:
            await self.channel.send(ADMIT_DEFEAT_MSG.format(self.attacker.name, self.defender.name))
            return await self.set_winner('d')
        elif self.result_reactions['d'] == 0:
            await self.channel.send(ADMIT_DEFEAT_MSG.format(self.defender.name, self.attacker.name))
            return await self.set_winner('a')
        elif self.result_reactions['a'] == 1:
            await self.claimed_victory('a', self.attacker, self.defender)
        elif self.result_reactions['d'] == 1:
            await self.claimed_victory('d', self.defender, self.attacker)

    async def ask_who_won(self):
        e = discord.Embed(color=discord.Color.green(),
                          title=START_GAME_TITLE.format(self.attacker.name, self.defender.name))
        e.add_field(name='Results', value=DUEL_RESULTS_MSG)
        msg = await self.channel.send(embed=e)
        await msg.add_reaction(self.client.usefulBasicEmotes['win'])
        await msg.add_reaction(self.client.usefulBasicEmotes['lose'])
        await msg.add_reaction(self.client.usefulBasicEmotes['no'])
        self.result_msg = msg

    async def enter_score(self, user, victory):
        who = None
        if user.id == self.attacker.id:
            who = 'a'
        elif user.id == self.defender.id:
            who = 'd'
        if not who:
            return False
        self.result_reactions[who] = victory
        await self.check_results()

    async def init_duel(self):
        e = discord.Embed(color=discord.Color.red(),
                          title=START_DUEL_TITLE.format(self.attacker.name, self.defender.name))
        e.set_thumbnail(url=self.attacker.avatar_url)
        e.set_image(url=self.defender.avatar_url)
        e.set_author(name=self.attacker, icon_url=self.attacker.avatar_url)
        e.add_field(name='Fight !', value=START_DUEL_MSG.format(self.attacker.mention))
        await self.channel.send("{} vs {}".format(self.attacker.mention, self.defender.mention), embed=e)

    async def delete_request_msg(self):
        if self.duelRequestMsg:
            await self.duelRequestMsg.delete()
            self.duelRequestMsg = None

    async def init_bracket(self):
        room_id, self.bracket = self.get_free_bracket()
        if not self.bracket:
            await self.client.log('No free bracket to play {} vs {}'.format(self.attacker, self.defender))
            return
        self.channel = self.client.usefulChannels[room_id]
        try:
            await self.attacker.add_roles(self.bracket)
            await self.defender.add_roles(self.bracket)
        except Exception as e:
            await self.client.log("Can't give {} role to {} or {}. {}".format(
                self.bracket.name, self.attacker, self.defender, e)
            )

    def get_free_bracket(self):
        for role in self.client.BracketRoles:
            if not len(self.client.BracketRoles[role].members):
                return role, self.client.BracketRoles[role]
        return None

    async def create(self):
        await self.init_bracket()
        await self.delete_request_msg()
        await self.init_duel()
        await self.ask_who_won()
