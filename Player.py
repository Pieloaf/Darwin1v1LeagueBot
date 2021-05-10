import discord
from EloCalculation import EloCalculation
from Ranks import set_rank, get_rank
from const import RankRoles, rolesValues


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
        
        updated_db_user = await self.client.usefulCogs['DB'].get_user(self.user.id)
        if updated_db_user['streak'] > updated_db_user['max_streak']:
            await self.client.usefulCogs['DB'].update_max_streak(self.user.id)

        if updated_db_user['victory']+updated_db_user['defeat'] >= 1:
            try: 
                for role in self.user.roles:
                    if role == self.client.usefulRoles['Unranked']:
                        await self.user.remove_roles(role)
                await set_rank(self.client, self.user, self.new_elo)
            except Exception:
                pass

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
        return self.get_text_for_player(self.db_user['elo'], self.new_elo)

    def check_unranked(self, loser):
        if  self.db_user['victory']+self.db_user['defeat'] < 1:
            winEloMsg = "Unranked"
        else:
            winEloMsg = f' won {self.get_update_elo_text()} elo'
        if  loser.db_user['victory']+loser.db_user['defeat'] < 1:
            loseEloMsg =  "Unranked"
        else:
            loseEloMsg = f' lose {loser.get_update_elo_text()} elo'
        return(winEloMsg, loseEloMsg)

    async def print_new_elos(self, loser, channel):
        e = discord.Embed(color=discord.Color.purple(), title="Elo update")
        eloMsg = self.check_unranked(loser)
        e.add_field(name=self.user.name, value=eloMsg[0])
        e.add_field(name=loser.user.name, value=eloMsg[1])
        await channel.send(embed=e)

    async def calculate_elos(self, loser):
        ranks = [a[0] for a in rolesValues]
        ranks.reverse()
        values = [a[1] for a in rolesValues]
        values.reverse()
        playedA = self.db_user['victory']+self.db_user['defeat']
        playedB =  loser.db_user['victory']+loser.db_user['defeat']
        elo_brain = EloCalculation(self.db_user['elo'], loser.db_user['elo'],playedA,playedB)

        for v in values:
            if self.db_user['elo'] < v:
                winRankIndex = values.index(v)-1
                break
        for v in values:
            if loser.db_user['elo'] < v:
                loseRankIndex = values.index(v)-1
                break

        if (winRankIndex-1 > loseRankIndex):
            streak_bonus = 0
        elif self.db_user['streak'] >= 5:
            streak_bonus = 5
        else:
            streak_bonus = self.db_user['streak']

        self.new_elo, loser.new_elo = elo_brain.calculate(1)
        self.new_elo = self.new_elo + streak_bonus

    async def get_db_user(self):
        self.db_user = await self.client.usefulCogs['DB'].get_user(self.user.id)
        return self.db_user

    async def log_beats(self, loser):
        winnerName = self.client.server.get_member(self.user.id).display_name
        if not winnerName:
            winnerName = self.user.name
        
        
        loserName = self.client.server.get_member(loser.user.id).display_name
        if not loserName:
            loserName = loser.user.name
        
        db_user = await self.client.usefulCogs['DB'].get_user(self.user.id)
        platform = db_user['platform']

        platformUrl = self.client.platformImages[platform]
        platformColour = self.client.platformColours[platform]

        embed = discord.Embed(
            color = discord.Colour(platformColour),
            title = f"{winnerName} beats {loserName}!",
        )
        eloMsg = self.check_unranked(loser)
        embed.add_field(name=eloMsg[0], value= f"<@{self.user.id}>", inline=True)
        embed.add_field(name=eloMsg[1], value= f"<@{loser.user.id}>", inline=True)
        embed.set_author(name="1v1 Results", icon_url = platformUrl)

        game = await self.client.usefulChannels['feed'].send(embed=embed) 
        await self.client.usefulCogs['DB'].add_game_to_db(game.id, self.user, loser.user, self.get_update_elo_text(), loser.get_update_elo_text())
    
    async def ping_sus_games(self, user):
        fast_games = await self.client.usefulCogs['DB'].sus_games(user)
        if  fast_games > 1:
            await self.client.usefulChannels['logs'].send(f"<@&780116909903183902> multiple games were played by <@{user}> in under 4 mins")

    async def wins(self, loser, channel):
        try:
            await self.get_db_user()
            await loser.get_db_user()
        except Exception as e:
            await self.client.log("Wins function failed, can find users in db", e)
        await self.calculate_elos(loser)
        await self.log_beats(loser)
        await self.ping_sus_games(self.user.id)
        await self.ping_sus_games(loser.user.id)
        await self.print_new_elos(loser, channel)
        await self.update_elo(True)
        await loser.update_elo(False)
