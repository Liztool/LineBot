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

# ===== LINE 推播 =====
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

# ===== 儲存目標日期（支援月/日） =====
def set_target(month, day):
    with open(TARGET_FILE, "w") as f:
        f.write(f"{month},{day}")

def get_target():
    if not os.path.exists(TARGET_FILE):
        return None, None
    with open(TARGET_FILE, "r") as f:
        m, d = f.read().split(",")
        return int(m), int(d)

# ===== 計算前一天 =====
def get_previous_date(month, day):
    today = datetime.date.today()
    target = datetime.date(today.year, month, day)
    prev = target - datetime.timedelta(days=1)
    return prev.month, prev.day

# ===== 更新 cron-job =====
def update_cron(month, day):
    cron_m, cron_d = get_previous_date(month, day)

    url = f"https://api.cron-job.org/jobs/{CRON_JOB_ID}"

    headers = {
        "Authorization": f"Bearer {CRON_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "job": {
            "enabled": True,
            "url": "https://linebot-rehab.onrender.com/cron",
            "requestMethod": "GET",
            "schedule": {
                "timezone": "Asia/Taipei",
                
                "hours": [9, 12, 18, 22],
                "minutes": [0],

                # 👉 關鍵：只指定「前一天」
                "mdays": [cron_d],
                "months": [cron_m],
            }
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

    if "/" in text:
        try:
            m, d = text.split("/")
            m = int(m)
            d = int(d)

            set_target(m, d)
            update_cron(m, d)

            send_message(f"📅 已設定 {m}/{d}（前一天提醒）")

        except:
            send_message("❌ 格式錯誤，例如：4/21")

    return "ok"

# ===== cron 觸發 =====
@app.route("/cron")
def cron_job():
    now = datetime.datetime.now()
    target_m, target_d = get_target()

    if not target_m:
        return "no target"

    tomorrow = now + datetime.timedelta(days=1)

    # 👉 判斷是否為前一天
    if tomorrow.month == target_m and tomorrow.day == target_d:
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