import discord
from discord.ext import commands
import random
import json
import asyncio
import os
from dotenv import load_dotenv 
import webserver

load_dotenv(".env")
TOKEN: str = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.help_command = None

message_counter = 0
spawn_threshold = 20
current_spawn = None
caught_data = {}
spawn_settings = {}

# Load and save functions
def load_data():
    global caught_data, spawn_settings
    try:
        with open("caught_data.json", "r") as f:
            caught_data = json.load(f)
    except FileNotFoundError:
        caught_data = {}

    try:
        with open("spawn_settings.json", "r") as f:
            spawn_settings = json.load(f)
    except FileNotFoundError:
        spawn_settings = {}

def save_data():
    with open("caught_data.json", "w") as f:
        json.dump(caught_data, f, indent=4)
    with open("spawn_settings.json", "w") as f:
        json.dump(spawn_settings, f, indent=4)

# Creatures
creatures = [
    {"name": "Bombardiro Crocodilo", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/1/10/Bombardiro_Crocodilo.jpg", "reward": 2100},
    {"name": "Tralalero Tralala", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/a/ac/Tralalero_tralala.jpg", "reward": 1000},
    {"name": "Brr Brr Patapim", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/f/f7/Brr_Brr_Patapim.png", "reward": 2000},
    {"name": "Lirili Larila", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/f/f1/Lirili_rili_ralila.png", "reward": 1500},
    {"name": "Scimpanzini Bananini", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/5/5c/ChimpanziniBananini.jpg", "reward": 2500},
    {"name": "Ballerina Cappuccina", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/8/8f/Videoframe_2657.png", "reward": 1800},
    {"name": "Bombombini Gusini", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/e/e3/Bombini_Gusini.jpg", "reward": 2200},
    {"name": "Frigo Cammello", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/a/a1/Frigo_Camelo.webp", "reward": 1700},
    {"name": "Trippi Troppi Troppa Trippa", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/6/62/Trippi_Troppi2.webp", "reward": 3000},
    {"name": "Tung Tung Tung Sahur", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/d/df/Anomali_tung_tung_tung.png", "reward": 1200},
    {"name": "Glorbo", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/7/72/Glorbofruttodrillo.jpeg", "reward": 1900},
    {"name": "Trulimero Trulicina", "image_url": "https://static.wikia.nocookie.net/brainrotnew/images/2/26/Trulimero_Trulichina.png", "reward": 1400}
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
    # Set the bot's activity (e.g., "Playing with code")
    activity = discord.Game(name="!help")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# Message tracking
@bot.event
async def on_message(message):
    global message_counter
    if message.author.bot:
        return

    await bot.process_commands(message)

    guild_id = str(message.guild.id)
    spawn_channel_id = spawn_settings.get(guild_id)
    if not spawn_channel_id:
        return

    message_counter += 1
    if message_counter >= spawn_threshold:
        message_counter = 0
        creature = random.choice(creatures)
        global current_spawn
        current_spawn = {
            "name": creature["name"],
            "image_url": creature["image_url"],
            "reward": creature["reward"],
            "channel_id": int(spawn_channel_id),
            "guild_id": guild_id
        }

        channel = bot.get_channel(current_spawn["channel_id"])
        if channel:
            embed = discord.Embed(
                title=f"🌟 A wild **{creature['name']}** appeared!",
                description="Type `!catch` to catch it! You have 60 seconds.",
                color=discord.Color.green()
            )
            embed.set_image(url=creature["image_url"])
            embed.set_footer(text="Be quick!")
            await channel.send(embed=embed)

            # Wait for 60 seconds before removing the creature if not caught
            await asyncio.sleep(60)
            if current_spawn and current_spawn["guild_id"] == guild_id:
                current_spawn = None
                embed = discord.Embed(
                    title="❌ Time's up!",
                    description="The wild creature escaped!",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

# Catch command
@bot.command()
async def catch(ctx):
    global current_spawn
    if not current_spawn or ctx.channel.id != current_spawn["channel_id"]:
        await ctx.send(embed=discord.Embed(
            title="❌ Nothing to catch!",
            description="No wild creature is currently here.",
            color=discord.Color.red()
        ))
        return

    user_id = str(ctx.author.id)
    caught_data.setdefault(user_id, {"caught": [], "currency": 0})
    caught_data[user_id]["caught"].append(current_spawn["name"])
    caught_data[user_id]["currency"] += current_spawn["reward"]
    save_data()

    embed = discord.Embed(
        title=f"🎉 {ctx.author.name} caught **{current_spawn['name']}**!",
        description=f"You earned {current_spawn['reward']} coins!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=current_spawn["image_url"])
    await ctx.send(embed=embed)
    current_spawn = None

# Balance
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    coins = caught_data.get(user_id, {"currency": 0})["currency"]
    embed = discord.Embed(
        title=f"{ctx.author.name}'s Balance",
        description=f"💰 {coins} coins",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# Collection
@bot.command()
async def collection(ctx):
    user_id = str(ctx.author.id)
    collection = caught_data.get(user_id, {"caught": []})["caught"]
    if not collection:
        embed = discord.Embed(
            title="📦 Your Collection",
            description="You haven't caught any creatures yet!",
            color=discord.Color.red()
        )
    else:
        desc = "\n".join(f"• {c}" for c in collection)
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Collection",
            description=desc,
            color=discord.Color.blue()
        )
    await ctx.send(embed=embed)

# Give coins
@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            title="Invalid Amount",
            description="Enter a positive number.",
            color=discord.Color.red()
        ))
        return

    caught_data.setdefault(sender_id, {"caught": [], "currency": 0})
    caught_data.setdefault(receiver_id, {"caught": [], "currency": 0})

    if caught_data[sender_id]["currency"] < amount:
        await ctx.send(embed=discord.Embed(
            title="Insufficient Funds",
            description="Not enough coins.",
            color=discord.Color.red()
        ))
        return

    caught_data[sender_id]["currency"] -= amount
    caught_data[receiver_id]["currency"] += amount
    save_data()

    embed = discord.Embed(
        title="💸 Transfer Successful",
        description=f"{ctx.author.name} gave {amount} coins to {member.display_name}.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Leaderboard
@bot.command()
async def leaderboard(ctx):
    if not caught_data:
        await ctx.send(embed=discord.Embed(
            title="Leaderboard",
            description="No data yet.",
            color=discord.Color.dark_gray()
        ))
        return

    sorted_users = sorted(caught_data.items(), key=lambda x: x[1].get("currency", 0), reverse=True)[:10]

    embed = discord.Embed(
        title="🌍 Global Leaderboard",
        description="Top 10 players by coins",
        color=discord.Color.purple()
    )

    for i, (user_id, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            embed.add_field(
                name=f"{i}. {user.name}",
                value=f"💰 {data.get('currency', 0)} coins",
                inline=False
            )
        except:
            continue

    await ctx.send(embed=embed)

# Admin: Set spawn channel
@bot.command()
@commands.has_permissions(administrator=True)
async def setspawnchannel(ctx):
    guild_id = str(ctx.guild.id)
    spawn_settings[guild_id] = ctx.channel.id
    save_data()
    await ctx.send(embed=discord.Embed(
        title="✅ Spawn Channel Set",
        description=f"Creatures will spawn in {ctx.channel.mention}.",
        color=discord.Color.green()
    ))

@setspawnchannel.error
async def setspawnchannel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            title="🚫 Permission Denied",
            description="Only admins can use this command.",
            color=discord.Color.red()
        ))

# Help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🛠️ Bot Help",
        description="List of available commands:",
        color=discord.Color.teal()
    )
    embed.add_field(name="!catch", value="Catch a creature.", inline=False)
    embed.add_field(name="!balance", value="Check your coin balance.", inline=False)
    embed.add_field(name="!collection", value="See your caught creatures.", inline=False)
    embed.add_field(name="!give @user <amount>", value="Give coins to another player.", inline=False)
    embed.add_field(name="!leaderboard", value="See the global top players.", inline=False)
    embed.add_field(name="!setspawnchannel", value="(Admin) Set creature spawn channel.", inline=False)
    embed.add_field(name="!help", value="Show this help message.", inline=False)
    await ctx.send(embed=embed)

webserver.keep_alive()
bot.run(TOKEN)
