import discord
from discord.ext import commands, tasks
import json
import datetime
import asyncio


class Daily(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.channel = None
    self.b = None
    self.myloop.start()

  
  @commands.Cog.listener()
  async def on_message(self, message):
    if message.channel == self.channel and not message.author.bot:
      
      try:
        await self.update_msg(message.author)
      except KeyError:
        await self.open(message.author)
        await self.update_msg(message.author)

  

  @commands.slash_command(guild_ids=[856054626137931776])
  async def start(self, ctx : discord.ApplicationContext, channel: discord.TextChannel):
    await ctx.defer()
    
    data = {}
    try:
      with open('daily.json', 'r') as f:
        data = json.load(f)
        
    except (FileNotFoundError, json.JSONDecodeError):
      pass

      if not data:
        a = str(datetime.datetime.now() + datetime.timedelta(days=30))
        data['time'] = a
        data['messages'] = {}
        with open('daily.json', 'w') as f:
          json.dump(data, f, indent=4)

    lb = await self.sort()
    guild = ctx.guild

    a = await self.get_webhook(ctx.channel)  

    output = await self.leaderboard(guild, lb)

    emb = discord.Embed(
      title="Monthly Leaderboard",
      description=f"Top 10 people with the most monthly messages.\n\n{output}",
      timestamp=datetime.datetime.now(),
      colour=0xFFAE00
    )
    emb.set_footer(text='Last Update')
    emb.set_thumbnail(url=ctx.guild.icon.url)
    emb.set_image(url='https://media.discordapp.net/attachments/932675355414761472/1118961426011275315/New_Project_39_228D72F.png?width=1246&height=701')
    
    b = await a.send(embed=emb, wait=True)

    await ctx.respond(f"Leaderboard is up and running in channel <#{ctx.channel.id}> and will only count messages sent in <#{channel.id}>.", ephemeral =True)

    self.channel = channel
    self.b = b


  @commands.slash_command(guild_ids=[856054626137931776])
  async def reset(self, ctx: discord.ApplicationContext):
    await ctx.defer()
    
    with open('daily.json', 'r') as f:
        data = json.load(f)
    
    if not data:
      await ctx.respond("The leaderboard has already been reset.", ephemeral=True)
      return
    
    leaderboard = await self.sort()
    member_id = leaderboard[0][0]
    member = ctx.guild.get_member(int(member_id))
    
    await ctx.channel.send(f"The most active member of the week is {member.mention}!")
    
    data.clear()
    
    with open('daily.json', 'w') as f:
      json.dump(data, f, indent=4)
    
    await ctx.respond("The leaderboard has been reset.", ephemeral=True)

  
  @commands.slash_command(guild_ids=[856054626137931776])
  async def addmessages(self, ctx: discord.ApplicationContext, user:
                        discord.Member, amount: int):
    await ctx.defer()
    
    if amount <= 0:
      await ctx.respond("Please enter a positive number of messages to add.", ephemeral=True)
      return
    
    await self.update_messages(user, amount)
    
    await ctx.respond(f"{amount} messages have been added to {user.mention}.", ephemeral=True)


  @commands.slash_command(guild_ids=[856054626137931776])
  async def removemessages(self, ctx: discord.ApplicationContext, user:
                           discord.Member, amount: int):
    await ctx.defer()
    
    if amount <= 0:
      await ctx.respond("Please enter a positive number of messages to remove.", ephemeral=True)
      return
    
    await self.update_messages(user, -amount)
    
    await ctx.respond(f"{amount} messages have been removed from {user.mention}.", ephemeral=True)

  

  @tasks.loop(minutes=5)
  async def myloop(self):
    await self.client.wait_until_ready()

    if self.channel is None:
      return
      
    await self.check(self.channel)

    lb = await self.sort()

    output = await self.leaderboard(self.channel.guild, lb)

    emb = discord.Embed(
      title="Monthly Leaderboard",
      description=f"Top 10 people with the most monthly messages.\n\n{output}",
      timestamp=datetime.datetime.now(),
      colour=0xFFAE00
    )
    emb.set_footer(text='Last Update')
    emb.set_thumbnail(url=self.channel.guild.icon.url)
    emb.set_image(url='https://media.discordapp.net/attachments/932675355414761472/1118961426011275315/New_Project_39_228D72F.png?width=1246&height=701')

    webhook = await self.get_webhook(self.channel)  # Retrieve or create webhook for the channel
    await self.update_webhook(self.b, emb)

    
    msgs = await self.get_msg()
    last_reset = datetime.datetime.strptime(msgs['time'], "%Y-%m-%d %H:%M:%S")
    current_time = datetime.datetime.now()
    
    
    if (current_time - last_reset).days >= 7:
      member_id = lb[0][0]
      member = self.channel.guild.get_member(int(member_id))
        
        
      await self.channel.send(f"The most active member of the week is {member.mention}!")
        
      msgs.clear()
      
      with open("daily.json", "w") as f:
        json.dump(msgs, f, indent=4)


  async def update_messages(self, user: discord.Member, amount: int):
    msgs = await self.get_msg()

    if str(user.id) in msgs["messages"]:
      msgs["messages"][str(user.id)] += amount
    else:
      msgs["messages"][str(user.id)] = amount
    
    with open("daily.json", "w") as f:
      json.dump(msgs, f, indent=4)

  
  async def get_webhook(self, channel):
    webhooks = await channel.webhooks()
    webhook = next((w for w in webhooks if w.user.id == self.client.user.id), None)
    if webhook:
      return webhook
    else:
      return await channel.create_webhook(name="Leaderboard Webhook")

  async def open(self, user):
    msgs = await self.get_msg()

    if str(user.id) in msgs["messages"]:
      return False

    msgs["messages"][str(user.id)] = 0

    with open("daily.json", "w") as f:
      json.dump(msgs, f, indent=4)

    return True

  async def get_msg(self):
    with open("daily.json", "r") as f:
      msgs = json.load(f)

      return msgs

  async def update_msg(self, user):
    msgs = await self.get_msg()

    if str(user.id) in msgs["messages"]:
      msgs["messages"][str(user.id)] += 1
    
    else:
      msgs["messages"][str(user.id)] = 1

    with open("daily.json", "w") as f:
      json.dump(msgs, f, indent=4)
      

  async def update_webhook(self, b, embed):
    try:   
      await b.edit(embed=embed)
      
    except discord.HTTPException as e:
      if e.code == 429:  # Rate limited
        retry_after = e.retry_after
        print(f'Rate limited. Retrying after {retry_after} seconds...')
        await asyncio.sleep(retry_after)
        await self.update_webhook(b, embed)
      else:
        print(f'Failed to update webhook: {e}')

  
  async def check(self, channel):
    msgs = await self.get_msg()

    if 'time' not in msgs:
      msgs['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if msgs['time'] == datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
      return

    guild = channel.guild

    lb = await self.sort()

    output = await self.leaderboard(guild, lb)

    emb = discord.Embed(
      title="Monthly Leaderboard",
      description=f"Top 10 people with the most monthly messages.\n\n{output}",
      timestamp=datetime.datetime.now(),
      colour=0xFFAE00
    )
    emb.set_footer(text='Last Update')
    emb.set_thumbnail(url=self.channel.guild.icon.url)
    emb.set_image(url='https://media.discordapp.net/attachments/932675355414761472/1118961426011275315/New_Project_39_228D72F.png?width=1246&height=701')

    await self.b.edit(embed=emb)

    msgs['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("daily.json", "w") as f:
      json.dump(msgs, f, indent=4)


  async def sort(self):
    msgs = await self.get_msg()

    if 'messages' not in msgs:
      msgs['messages'] = {}

    msgs = msgs['messages']

    return sorted(msgs.items(), key=lambda x: x[1], reverse=True)


  async def leaderboard(self, guild, lb):
    output = ""

    one = '<a:verblacknyellow:1118940641519476746>'
    two = '<a:verred:1118940690743824535>'
    four = '<a:green:1118944797458186241>'
    six = '<a:Verified:1118940771916193834>'
    msg = '<:AWK_x_message:938740837855133727>'
    
    i = 0
    for member_id, vals in (x for x in lb[:10]):
      i += 1
      member = guild.get_member(int(member_id))

      if i == 1:
        output += f'{one} `[{i}]` **{member}**\n{msg} `{vals} messages`\n\n'
      elif i > 1 and i <= 3:
        output += f'{two} `[{i}]` **{member}**\n{msg} `{vals} messages`\n\n'
      elif i > 3 and i <= 5:
        output += f'{four} `[{i}]` **{member}**\n{msg} `{vals} messages`\n\n'
      elif i > 5:
        output += f'{six} `[{i}]` **{member}**\n{msg} `{vals} messages`\n\n'
    
    return output

def setup(client):
  client.add_cog(Daily(client))