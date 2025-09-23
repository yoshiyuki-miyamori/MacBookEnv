DISCORD_TOKEN = "自分のDiscordのBotのトークンを貼り付ける"
CHANNEL_ID = 0000000000000000000 # 通知を送信したい自分のDiscordチャンネルのIDを貼り付ける
ARXIV_CATEGORY = "stat.TH" # statistics theory
MAX_RESULTS = 50
CHECK_START_HOUR = 9
CHECK_END_HOUR = 15

import discord
import requests
import xml.etree.ElementTree as ET
import datetime
import asyncio
import os

ARXIV_API_URL = f"http://export.arxiv.org/api/query?search_query=cat:{ARXIV_CATEGORY}&sortBy=submittedDate&sortOrder=descending&max_results={MAX_RESULTS}"
bot = discord.Client(intents=discord.Intents.default())
Japan_Standard_Time = datetime.timezone(datetime.timedelta(hours=9))

def Current_Papers():
    current_papers = []
    for entry in ET.fromstring(requests.get(ARXIV_API_URL).content).findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
        paper_id, version = entry.find("{http://www.w3.org/2005/Atom}id").text.split("/abs/")[-1].split('v')
        if version == '1':
            current_papers.append((title, paper_id))
    return current_papers

def Seen_Papers():
    if not os.path.exists("seen_papers.txt"):
        with open("seen_papers.txt", "w") as seen_papers:
            current_v1_paper_ids = [paper_id for _, paper_id in Current_Papers()]
            seen_papers.writelines(f"{paper_id}\n" for paper_id in current_v1_paper_ids)
    with open("seen_papers.txt", "r") as seen_papers:
        seen_paper_ids = {paper_id.strip() for paper_id in seen_papers}
    return seen_paper_ids

@bot.event
async def on_ready():
    print("arXivの更新を待っています...")
    await bot.change_presence(status=discord.Status.invisible) # オフライン表示にする
    while not bot.is_closed():
        now = datetime.datetime.now(Japan_Standard_Time)
        start_time = now.replace(hour=CHECK_START_HOUR, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=CHECK_END_HOUR, minute=0, second=0, microsecond=0)
        weekend = now.weekday() in [5, 6]

        if not weekend and start_time <= now <= end_time:
            try:
                current_papers = Current_Papers()
                seen_paper_ids = Seen_Papers()
                new_papers = []

                for title, paper_id in current_papers:
                    if paper_id not in seen_paper_ids:
                        new_papers.append((title, paper_id))
                        with open("seen_papers.txt", "a") as seen_papers:
                            seen_papers.write(f"{paper_id}\n")

                for title, paper_id in new_papers:
                    alphaXiv_URL = f"https://www.alphaxiv.org/ja/overview/{paper_id}"
                    await bot.get_channel(CHANNEL_ID).send(embed=discord.Embed(title=title, description=f"<{alphaXiv_URL}>") )

            except Exception as e:
                print(f"Error: {e}")

        await asyncio.sleep(600) # 長時間スリープさせるとDiscordとの接続が不安定になる

bot.run(DISCORD_TOKEN)