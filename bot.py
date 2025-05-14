import discord
from discord.ext import tasks
import aiohttp
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from flask import Flask
from threading import Thread

# Flask app to keep the bot alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Setup intents and bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# Slash command version of /weather
@tree.command(name="weather", description="Get the weather for a city")
@discord.app_commands.describe(city="City to get weather for")
async def weather(interaction: discord.Interaction, city: str):
    async with aiohttp.ClientSession() as session:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        async with session.get(url) as response:
            data = await response.json()
            if response.status == 200:
                weather_data = data['main']
                weather_desc = data['weather'][0]['description']
                temp = weather_data['temp']
                humidity = weather_data['humidity']
                embed = discord.Embed(title=f"Weather in {city}", color=discord.Color.blue())
                embed.add_field(name="Temperature", value=f"{temp}°C", inline=False)
                embed.add_field(name="Humidity", value=f"{humidity}%", inline=False)
                embed.add_field(name="Description", value=weather_desc.capitalize(), inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Couldn't fetch weather data for {city}. Please try again later.")

# Scheduled maintenance message every Saturday 8 PM EST
@tasks.loop(hours=168)
async def send_maintenance_message():
    now = datetime.datetime.now()
    next_saturday = now + datetime.timedelta((5 - now.weekday()) % 7)
    next_saturday_8pm = next_saturday.replace(hour=20, minute=0, second=0, microsecond=0)
    await discord.utils.sleep_until(next_saturday_8pm)
    
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🚧 **The Minecraft server is under maintenance every Saturday at 8 PM EST!** 🚧")

# On ready: sync commands and start task
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user} and slash commands synced.")
    send_maintenance_message.start()

# Start everything
keep_alive()
bot.run(TOKEN)