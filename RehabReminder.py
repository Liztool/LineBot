from flask import Flask, request
import requests
import datetime
import os

app = Flask(__name__)

# ===== 環境變數 =====
CHANNEL_ACCESS_TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")

CRON_API_KEY = os.getenv("CRON_API_KEY")
CRON_JOB_ID = os.getenv("CRON_JOB_ID")

TARGET_FILE = "target_day.txt"

# ===== 工具 =====
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

def get_target_day():
    if not os.path.exists(TARGET_FILE):
        return 25
    with open(TARGET_FILE, "r") as f:
        return int(f.read())

def set_target_day(day):
    with open(TARGET_FILE, "w") as f:
        f.write(str(day))

# 👉 修正月份問題（1號 → 上個月最後一天）
def get_previous_day(target_day):
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)

    if target_day == 1:
        return last_day_prev_month.day
    else:
        return target_day - 1

# ===== 更新 cron-job =====
def update_cron(day):
    cron_day = get_previous_day(day)

    schedule = f"0 9,12,18,22 {cron_day} * *"

    url = f"https://api.cron-job.org/jobs/{CRON_JOB_ID}"

    headers = {
        "Authorization": f"Bearer {CRON_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "job": {
            "enabled": True,
            "schedule": schedule,
            "url": "https://你的網址.onrender.com/cron",
            "requestMethod": "GET"
        }
    }

    try:
        r = requests.patch(url, json=data, headers=headers)
        print("cron update status:", r.status_code)
        print("cron response:", r.text)

        if r.status_code != 200:
            send_message("⚠️ cron 更新失敗，請檢查設定")
        else:
            send_message(f"✅ cron 已更新：前一天 {cron_day} 號")

    except Exception as e:
        print("cron error:", str(e))
        send_message("❌ cron 更新錯誤")

# ===== LINE webhook =====
@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.json

    try:
        event = data["events"][0]
        text = event["message"]["text"]
    except:
        return "ok"

    if text.startswith("設定"):
        try:
            day = int(text.replace("設定", "").strip())

            if 1 <= day <= 31:
                set_target_day(day)
                update_cron(day)
                send_message(f"📅 已設定每月 {day} 號")
            else:
                send_message("❌ 請輸入 1~31")

        except:
            send_message("❌ 格式錯誤，例如：設定 25")

    return "ok"

# ===== cron 觸發 =====
@app.route("/cron")
def cron_job():
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)

    target_day = get_target_day()

    if tomorrow.day == target_day:
        hour = now.hour

        if hour == 9:
            send_message("🌅 早安提醒")
        elif hour == 12:
            send_message("🍱 中午提醒")
        elif hour == 18:
            send_message("🌆 晚上提醒")
        elif hour == 22:
            send_message("🌙 睡前提醒")

    return "ok"

@app.route("/")
def home():
    return "ok"