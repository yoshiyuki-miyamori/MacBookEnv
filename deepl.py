import discord
import requests

Discord_Token = "自分のDiscordのBotのトークンを貼り付ける"

# --- リアクションと言語の対応 ---
FLAG_TO_LANG = {
    '🇺🇸': 'EN-US',
    '🇬🇧': 'EN-GB',
    '🇯🇵': 'JA',
    '🇨🇳': 'ZH',
    '🇰🇷': 'KO',
    '🇩🇪': 'DE',
    '🇫🇷': 'FR',
    '🇮🇹': 'IT',
    '🇪🇸': 'ES',
    '🇷🇺': 'RU',
}

# --- Discord Botの初期設定 ---
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容を読み取るために必要
intents.reactions = True      # リアクションを検知するために必要

client = discord.Client(intents=intents)

# --- Botの動作 ---

# 起動時動作
@client.event
async def on_ready():
    print("リアクション待機中...")
        
# 翻訳関連動作
@client.event
async def on_raw_reaction_add(payload):
    # Bot自身のリアクションは無視
    if payload.user_id == client.user.id:
        return

    # 対応する絵文字でなければ処理を終了
    target_emoji = str(payload.emoji)
    if target_emoji not in FLAG_TO_LANG:
        return

    DeepL_Token = "自分のDeepLのAPIキーを貼り付ける"
    DeepL_API_URL = "https://api-free.deepl.com/v2/translate"

    try:
        # リアクションした本人を取得
        user = await client.fetch_user(payload.user_id)
        
        # リアクションされたメッセージを取得
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        params = {
            "auth_key": DeepL_Token,
            "text": message.content,
            "target_lang": FLAG_TO_LANG[target_emoji]
            # source_langは指定せず、DeepLの自動検出に任せる
        }

        # DeepL APIにリクエストを送信
        response = requests.post(DeepL_API_URL, data=params)

        # リクエスト成功時
        if response.status_code == 200:
            response_json = response.json()
            translated_text = response_json["translations"][0]["text"]
            
            # 元のメッセージの引用を作成
            original_message_quote = f"> 「{message.content[:50]}...」\n" if len(message.content) > 50 else f"> 「{message.content}」\n"
            
            # 本人にDMで翻訳結果を送信
            await user.send(f"{original_message_quote}{translated_text}")
        
        # リクエスト失敗時
        else:
            error_message = f"翻訳エラー(DeepL): {response.status_code}{response.text}"
            print(error_message)
            await user.send(error_message)

    except Exception as e:
        error_message = f"処理中に予期せぬエラーが発生しました: {e}"
        print(error_message)
        # ユーザーオブジェクトがまだ取得できていない可能性を考慮
        try:
            user = await client.fetch_user(payload.user_id)
            await user.send(error_message)
        except Exception as inner_e:
            print(f"エラー通知の送信に失敗しました: {inner_e}")


client.run(Discord_Token)
