import discord
import os
from keep_alive import keep_alive
import asyncio


intents = discord.Intents.default()
intents.members = True
intents.presences = True
client = discord.Bot(debug_guilds=[856054626137931776],intents=intents)


for filename in os.listdir('./cogs'):
  if filename.endswith('.py'):             
    client.load_extension(f'cogs.{filename[:-3]}')


@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))


@client.event
async def on_disconnect():
  print('Disconnected from Discord. Reconnecting...')
  while not client.is_closed():
    try:
      await client.start(os.environ['token'])
      break
    except Exception as e:
      print(f'Failed to reconnect: {e}')
      await asyncio.sleep(5)

keep_alive()
client.run(os.environ['token'])