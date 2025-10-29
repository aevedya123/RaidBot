import os
import discord
import asyncio
from discord.ext import tasks
from datetime import datetime, timezone
import requests
import re

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# store already seen links to prevent duplicates
seen_links = set()

@client.event
async def on_ready():
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user}")
    post_links.start()

@tasks.loop(minutes=1)
async def post_links():
    try:
        headers = {".ROBLOSECURITY": ROBLOX_COOKIE}
        resp = requests.get(f"https://groups.roblox.com/v1/groups/{SERVER_ID}/wall/posts", headers=headers)

        if resp.status_code != 200:
            print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status_code}")
            return

        data = resp.json().get("data", [])
        new_links = []

        for post in data:
            content = post.get("body", "")
            links = re.findall(r'https?://\S+', content)
            for link in links:
                if link not in seen_links:
                    seen_links.add(link)
                    new_links.append(link)

        if new_links:
            channel = client.get_channel(CHANNEL_ID)
            combined = "\n".join(new_links)
            embed = discord.Embed(
                title="🧩 New Roblox Links Found",
                description=combined,
                color=0x2F3136,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Made by SAB-RS")
            await channel.send(embed=embed)

        else:
            print(f"[{datetime.now(timezone.utc)}] No new links found.")

    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] Error: {e}")

client.run(DISCORD_TOKEN)
