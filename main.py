import os
import requests
import discord
from discord.ext import tasks
from flask import Flask
import threading
import types
import sys
from datetime import datetime

sys.modules['audioop'] = types.SimpleNamespace()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("SERVER_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def get_group_links():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    resp = requests.get(url, headers=headers)
    print(f"[{datetime.utcnow()}] Roblox API status: {resp.status_code}")
    if resp.status_code != 200:
        return []
    data = resp.json()
    links = []
    for post in data.get("data", []):
        content = post.get("body", "")
        for word in content.split():
            if word.startswith("https://"):
                links.append(word)
    print(f"[{datetime.utcnow()}] Found links: {links}")
    return links

@tasks.loop(minutes=5)
async def send_links():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"[{datetime.utcnow()}] Channel not found!")
        return
    links = get_group_links()
    if not links:
        print(f"[{datetime.utcnow()}] No links found to send.")
        return
    embed = discord.Embed(
        title="New Roblox Links",
        description="\n".join(links),
        color=discord.Color.blue()
    )
    embed.set_footer(text="Made by SAB-RS")
    await channel.send(embed=embed)
    print(f"[{datetime.utcnow()}] ✅ Sent embed with {len(links)} links")

@client.event
async def on_ready():
    print(f"[{datetime.utcnow()}] ✅ Logged in as {client.user}")
    send_links.start()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
