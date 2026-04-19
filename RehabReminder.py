from flask import Flask, request
import requests
import datetime
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")

# 用檔案存目標日（簡單版）
TARGET_FILE = "target_day.txt"

def get_target_day():
    if not os.path.exists(TARGET_FILE):
        return 25  # 預設
    with open(TARGET_FILE, "r") as f:
        return int(f.read())

def set_target_day(day):
    with open(TARGET_FILE, "w") as f:
        f.write(str(day))

def send_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=data)

# 🔹 LINE webhook（用來設定日期）
@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.json
    event = data["events"][0]
    text = event["message"]["text"]

    if text.startswith("設定"):
        try:
            day = int(text.replace("設定", "").strip())
            if 1 <= day <= 31:
                set_target_day(day)
                send_message(f"已設定每月 {day} 號")
            else:
                send_message("請輸入1~31")
        except:
            send_message("格式錯誤，例如：設定 25")

    return "ok"

# 🔹 cron 觸發（一天4次）
@app.route("/cron")
def cron_job():
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)

    target_day = get_target_day()

    if tomorrow.day == target_day:
        hour = now.hour

        if hour == 9:
            send_message("早安提醒")
        elif hour == 12:
            send_message("中午提醒")
        elif hour == 18:
            send_message("晚上提醒")
        elif hour == 22:
            send_message("睡前提醒")

    return "ok"

@app.route("/")
def home():
    return "ok"