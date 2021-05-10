from discord.ext import commands
import discord

class LogsCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot:
            return
        db_user = await self.client.usefulCogs['DB'].get_user(before.id)
        if not db_user:
            await self.client.log(f'could not get {before.id}')
            return
        elif db_user['victory'] + db_user['defeat'] < 1:
            return
        for role in self.client.RankRoles:
            wasAttributed = self.client.RankRoles[role] in before.roles
            isAttributed = self.client.RankRoles[role] in after.roles

            if not wasAttributed and isAttributed:
                if db_user['streak'] > 0:
                    imgURL = "https://cdn.discordapp.com/attachments/787098837516812369/787135511411163136/rnkup.png"
                    embdCol = self.client.RankRoles[role].color.value
                    embdTitle = "Rank Up!"
                    change = "Ranked Up"
                else:
                    imgURL = "https://cdn.discordapp.com/attachments/787098837516812369/787135942283493426/rnkdwn.png"
                    embdCol = self.client.RankRoles[role].color.value
                    embdTitle = "Rank Down"
                    change = "Ranked Down"

                embed = discord.Embed(
                    color = discord.Colour(embdCol),
                    title = embdTitle,
                    description = f"{after.mention} {change} to {self.client.RankRoles[role].name}"
                )
                embed.set_author(name=after.display_name, icon_url=after.avatar_url)
                embed.set_thumbnail(url=imgURL)

                msgtoPublish = await self.client.usefulChannels['feed'].send(embed=embed)
                await msgtoPublish.publish()
                return


def setup(client):
    client.add_cog(LogsCog(client))
