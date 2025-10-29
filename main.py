import discord
import asyncio
import requests
import os
import sys
import time
from datetime import datetime, timezone

# ==========================
# ENVIRONMENT VARIABLES
# ==========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")

# ==========================
# DISCORD CLIENT
# ==========================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# track previously posted links
posted_links = set()

# ==========================
# FETCH LINKS FUNCTION
# ==========================
def fetch_links():
    headers = {".ROBLOSECURITY": ROBLOX_COOKIE}
    url = f"https://groups.roblox.com/v1/groups/{SERVER_ID}/wall/posts"

    try:
        resp = requests.get(url, cookies=headers, timeout=10)
        if resp.status_code != 200:
            print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status_code}")
            return []

        data = resp.json()
        links = []

        for post in data.get("data", []):
            body = post.get("body", "")
            for word in body.split():
                if word.startswith("https://www.roblox.com/share?code="):
                    links.append({
                        "link": word,
                        "poster": post.get("poster", {}).get("username", "Unknown"),
                        "created": post.get("created", None)
                    })
        return links

    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] ❌ Error fetching links: {e}")
        return []

# ==========================
# MAIN LOOP
# ==========================
async def monitor_links():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("⚠️ Channel not found. Check CHANNEL_ID.")
        return

    print(f"[{datetime.now(timezone.utc)}] ✅ Monitoring group wall...")

    while not client.is_closed():
        try:
            new_links = await asyncio.to_thread(fetch_links)
            if not new_links:
                print(f"[{datetime.now(timezone.utc)}] No new links found.")
                await asyncio.sleep(60)
                continue

            count = 0
            for post in new_links:
                if count >= 30:
                    break

                link = post["link"]
                if link not in posted_links:
                    posted_links.add(link)
                    count += 1

                    embed = discord.Embed(
                        title="📎 New Private Server Link",
                        description=f"[Click to join]({link})",
                        color=discord.Color.blurple(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="Posted by", value=post["poster"], inline=True)
                    embed.set_footer(text="Made by SAB-RS")

                    try:
                        await channel.send(embed=embed)
                        print(f"[{datetime.now(timezone.utc)}] Sent: {link}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"[{datetime.now(timezone.utc)}] ⚠️ Failed to send: {e}")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"[{datetime.now(timezone.utc)}] ⚠️ Loop error: {e}")
            print("⏳ Restarting monitor in 10 seconds...")
            await asyncio.sleep(10)

# ==========================
# RESTART PROTECTION
# ==========================
async def safe_start():
    retry = 0
    while retry < 10:
        try:
            await monitor_links()
            break
        except Exception as e:
            retry += 1
            print(f"⚠️ Crash #{retry}: {e}. Restarting in 10s...")
            await asyncio.sleep(10)
    print("❌ Too many failures. Exiting.")
    sys.exit(1)

# ==========================
# STARTUP
# ==========================
@client.event
async def on_ready():
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user}")

client.loop.create_task(safe_start())
client.run(DISCORD_TOKEN)
