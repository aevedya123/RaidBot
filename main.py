import os
import requests
import discord
from discord.ext import tasks
from flask import Flask
import threading
import types
import sys

# ---- Ignore audioop ----
sys.modules['audioop'] = types.SimpleNamespace()

# ---- ENV VARIABLES ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("SERVER_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# ---- Discord bot setup ----
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---- Flask app to keep alive ----
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---- Function to get Roblox group wall posts ----
def get_group_links():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    data = response.json()
    links = []
    for post in data.get("data", []):
        content = post.get("body", "")
        for word in content.split():
            if word.startswith("https://"):
                links.append(word)
    return links

# ---- Discord task loop ----
@tasks.loop(minutes=5)
async def send_links():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return
    links = get_group_links()
    if links:
        embed = discord.Embed(
            title="New Roblox Links",
            description="\n".join(links),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Made by SAB-RS")
        await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    send_links.start()

# ---- Run both Flask and Discord ----
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
