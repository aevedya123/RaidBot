import os
import re
import discord
import aiohttp
import asyncio
from datetime import datetime, timezone
from discord import Embed
from flask import Flask
import threading
import types
import sys

# Prevent audioop import error on Python 3.13
sys.modules["audioop"] = types.SimpleNamespace()

# --- Environment Variables ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# --- Flask Keep-Alive Webserver ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Track last seen post to avoid duplicates
last_post_id = None

async def fetch_group_posts():
    """Fetch recent posts from the Roblox group wall."""
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    url = f"https://groups.roblox.com/v2/groups/{SERVER_ID}/wall/posts?limit=30&sortOrder=Desc"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status}")
                return []
            data = await resp.json()
            return data.get("data", [])

def extract_links(text):
    """Extract Roblox share links from text."""
    return re.findall(r"https?://www\.roblox\.com/share\?code=[A-Za-z0-9]+&type=Server", text)

async def send_links_to_discord(links):
    """Send extracted links to Discord as embeds."""
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found. Check CHANNEL_ID.")
        return

    for link in links:
        embed = Embed(
            title="🕹️ Private Server Link Found",
            description=f"[Join Server]({link})",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Made by SAB-RS")
        await channel.send(embed=embed)
        await asyncio.sleep(2)  # space out messages to avoid rate limits

@client.event
async def on_ready():
    global last_post_id
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user}")

    while True:
        try:
            posts = await fetch_group_posts()
            if not posts:
                await asyncio.sleep(60)
                continue

            new_links = []
            for post in posts:
                if last_post_id and post["id"] <= last_post_id:
                    continue
                links = extract_links(post["body"])
                new_links.extend(links)

            if posts:
                last_post_id = posts[0]["id"]

            if new_links:
                print(f"✅ Found {len(new_links)} new link(s)")
                await send_links_to_discord(new_links)
            else:
                print(f"[{datetime.now(timezone.utc)}] No new links found")

        except Exception as e:
            print(f"⚠️ Error: {e}")

        await asyncio.sleep(60)  # check every minute


client.run(DISCORD_TOKEN)
