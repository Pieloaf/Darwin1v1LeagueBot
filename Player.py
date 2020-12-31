import discord
from EloCalculation import EloCalculation
from Ranks import set_rank


class Player:
    def __init__(self, client, member):
        self.user = member
        self.client = client
        self.db_user = None
        self.new_elo = None

    async def update_elo(self, wins):
        if wins:
            await self.client.usefulCogs['DB'].wins(self.user.id, self.new_elo)
        else:
            await self.client.usefulCogs['DB'].lose(self.user.id, self.new_elo)
        if  self.db_user['victory']+self.db_user['defeat'] < 10:
            return
        await set_rank(self.client, self.user, self.new_elo)

    @staticmethod
    def get_text_for_player(elo, new_elo):
        msg = ''
        diff = new_elo - elo
        if diff > 0:
            msg += str(diff)
        else:
            msg += str(abs(diff))
        return msg

    def get_update_elo_text(self):
        if  self.db_user['victory']+self.db_user['defeat'] < 10:
            return "unranked"    
        return self.get_text_for_player(self.db_user['elo'], self.new_elo)
        

    async def print_new_elos(self, loser, channel):
        e = discord.Embed(color=discord.Color.purple(), title="Elo update")
        e.add_field(name=self.user.name, value=f' won {self.get_update_elo_text()} elo ')
        e.add_field(name=loser.user.name, value=f' lose {loser.get_update_elo_text()} elo ')
        await channel.send(embed=e)

    async def calculate_elos(self, loser):
        elo_brain = EloCalculation(self.db_user['elo'], loser.db_user['elo'])
        if self.db_user['streak'] >= 5:
            streak_bonus = 5
        else:
            streak_bonus = self.db_user['streak']
        self.new_elo, loser.new_elo = elo_brain.calculate(1)
        self.new_elo = self.new_elo + streak_bonus

    async def get_db_user(self):
        self.db_user = await self.client.usefulCogs['DB'].get_user(self.user.id)
        return self.db_user

    async def log_beats(self, loser):
        winner = self.client.server.get_member(self.user.id)
        loserMem = self.client.server.get_member(loser.user.id)
        platforms = ['PC', 'PS4', 'Xbox']

        for role in winner.roles:
            if role.name in platforms:
                platformUrl = self.client.platformImages[role.name]
                platformColour = self.client.platformColours[role.name]

        embed = discord.Embed(
            color = discord.Colour(platformColour),
            title = f"{winner.display_name} beats {loserMem.display_name}!",
        )
        embed.add_field(name=f"{winner.mention}", value= f"+{self.get_update_elo_text()} elo", inline=True)
        embed.add_field(name=f"{loserMem.mention}", value= f"-{loser.get_update_elo_text()} elo", inline=True)
        embed.set_author(name="1v1 Results", icon_url = platformUrl)

        msgtoPublish = await self.client.usefulChannels['feed'].send(embed=embed)
        await msgtoPublish.publish()

    async def wins(self, loser, channel):
        try:
            await self.get_db_user()
            await loser.get_db_user()
        except Exception as e:
            await self.client.log("Wins function failed, can find users in db", e)
        await self.calculate_elos(loser)
        await self.log_beats(loser)
        await self.print_new_elos(loser, channel)
        await self.update_elo(True)
        await loser.update_elo(False)
