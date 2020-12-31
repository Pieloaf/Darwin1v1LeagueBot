from DarwinBot import DarwinBot
import os
import discord

with open('./botToken') as file:
    botToken = file.readlines()

intents = discord.Intents.all()

client = DarwinBot(command_prefix='.', intents=intents)
client.remove_command('help')
client.run(f'{botToken[0]}')
