DISCORD_TOKEN = "自分のDiscordのBotのトークンを貼り付ける"
CHANNEL_ID = 自分のチャンネルIDを貼り付ける  # 通知を送信したいDiscordチャンネルのID
ARXIV_CATEGORY = "stat.TH"  # チェックするarXivのカテゴリ = statistics theory
CHECK_START_HOUR = 8 # チェックを開始する時刻
CHECK_END_HOUR = 12 # チェックを終了する時刻

import discord
import requests
import xml.etree.ElementTree as ET
import datetime
import asyncio
import os

ARXIV_API_URL = f"http://export.arxiv.org/api/query?search_query=cat:{ARXIV_CATEGORY}&sortBy=submittedDate&sortOrder=descending&max_results=50"
bot = discord.Client(intents=discord.Intents.default())
JST = datetime.timezone(datetime.timedelta(hours=9)) # 日本時間

# チェック済みリストがまだない時は現在の論文リストとして作成
if not os.path.exists("seen_papers.txt"):
    with open("seen_papers.txt", "w") as seen_papers:
        for entry in ET.fromstring(requests.get(ARXIV_API_URL).content).findall("{http://www.w3.org/2005/Atom}entry"):
            paper_id = entry.find("{http://www.w3.org/2005/Atom}id").text.split("/abs/")[-1]
            seen_papers.write(f"{paper_id}\n")

# Botの動作
@bot.event
async def on_ready():
    print("arXivの更新を待っています...")
    while not bot.is_closed():
        now = datetime.datetime.now(JST)
        start_time = now.replace(hour=CHECK_START_HOUR, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=CHECK_END_HOUR, minute=0, second=0, microsecond=0)

        # 今が平日かつ活動時間内の時
        if now.weekday() not in [5, 6] and start_time <= now <= end_time:
            new_papers_found = False
            try:
                with open("seen_papers.txt", "r+") as seen_papers:
                    seen_paper_ids = {line.strip() for line in seen_papers}
                    new_papers = []
                    current_papers = set()

                # arXiv APIから論文IDを取得
                for entry in ET.fromstring(requests.get(ARXIV_API_URL).content).findall("{http://www.w3.org/2005/Atom}entry"):
                    paper_id = entry.find("{http://www.w3.org/2005/Atom}id").text.split("/abs/")[-1]
                    current_papers.add(paper_id) # current_papersに記録

                    # チェック済みか確認
                    if paper_id not in seen_paper_ids:
                        new_papers.append(entry) # new_papersに記録
                        new_papers_found = True

                    # 新着論文が見つかった場合はseen_papers.txtを全部書き直す
                    if new_papers_found:
                        seen_papers.seek(0); seen_papers.truncate() # 現在の中身を削除
                        seen_papers.writelines(f"{paper_id}\n" for paper_id in current_papers) # current_papersの中身をコピー

                    # new_papersのタイトルとURLを送信
                    for entry in new_papers:
                        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
                        overview_url = f"https://www.alphaxiv.org/ja/overview/{entry.find('{http://www.w3.org/2005/Atom}id').text.split('/abs/')[-1]}"
                        await bot.get_channel(CHANNEL_ID).send(embed=discord.Embed(title=title, description=f"<{overview_url}>") )

            except Exception as e:
                print(f"エラー: {e}")
            
            # 次の確認時刻は原則10分後だが，それが終了時刻をオーバーしている場合は翌日の開始時刻に設定
            next_check_time = now + datetime.timedelta(minutes=10)
            if next_check_time > end_time:
                next_day = now + datetime.timedelta(days=1)
                next_check_time = next_day.replace(hour=CHECK_START_HOUR, minute=0, second=0, microsecond=0)

        # 今が休日または活動時間外の時
        else:
            # 平日かつ開始時刻前なら次回の確認を開始時刻に設定
            if now.weekday() not in [5, 6] and now < start_time:
                next_check_time = start_time
            # (平日かつ終了時刻後)あるいは(休日)なら次の確認時刻を翌日の開始時刻に設定
            else:
                next_day = now + datetime.timedelta(days=1)
                next_check_time = next_day.replace(hour=CHECK_START_HOUR, minute=0, second=0, microsecond=0)

        # 次の確認時刻まで待機
        await asyncio.sleep((next_check_time - datetime.datetime.now(JST)).total_seconds())

bot.run(DISCORD_TOKEN)
