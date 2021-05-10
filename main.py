from DarwinBot import DarwinBot
import os
import discord
from tokens import bot_token

intents = discord.Intents.all()

client = DarwinBot(command_prefix='.', intents=intents)
client.remove_command('help')
client.run(bot_token)
