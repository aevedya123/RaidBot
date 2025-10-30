import os
import time
import requests
import discord
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def fetch_group_wall_posts():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "User-Agent": "Roblox/WinInet",
        "Accept": "application/json"
    }
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit=25"
    
    for attempt in range(5):
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if "data" in data:
                    return data["data"]
                else:
                    print("⚠️ Unexpected response:", data)
                    return []
            elif r.status_code == 429:
                print("⏳ Rate limited, waiting before retrying...")
                time.sleep(5)
            elif r.status_code >= 500:
                print("🚨 Roblox server error (500+), retrying...")
                time.sleep(3)
            else:
                print(f"⚠️ HTTP {r.status_code}: {r.text}")
                return []
        except Exception as e:
            print("❌ Request error:", e)
            time.sleep(3)
    return []

last_post_ids = set()

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    check_posts.start()

@tasks.loop(seconds=30)
async def check_posts():
    global last_post_ids
    posts = fetch_group_wall_posts()
    if not posts:
        return
    channel = client.get_channel(CHANNEL_ID)
    for post in reversed(posts):
        post_id = post.get("id")
        if post_id not in last_post_ids:
            content = post.get("body", "")
            user = post.get("poster", {}).get("username", "Unknown")
            if "roblox.com/" in content:
                await channel.send(f"🔗 **New link from {user}:** {content}")
            last_post_ids.add(post_id)
    # Limit memory
    if len(last_post_ids) > 200:
        last_post_ids = set(list(last_post_ids)[-100:])

client.run(TOKEN)
