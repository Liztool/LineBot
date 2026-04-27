from flask import Flask, request
import requests
import datetime
import os
import pytz

app = Flask(__name__)

# ===== 環境變數 =====
CHANNEL_ACCESS_TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")

CRON_API_KEY = os.getenv("CRON_API_KEY")
CRON_JOB_ID = os.getenv("CRON_JOB_ID")
COLD_CRON_JOB_ID = os.getenv("COLD_CRON_JOB_ID")

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

# ===== 計算前一天 =====
def get_previous_date(month, day):
    today = datetime.date.today()
    target = datetime.date(today.year, month, day)
    prev = target - datetime.timedelta(days=1)
    return prev.month, prev.day

# ===== 更新 cron-job =====
def update_cron(month, day, hour, minute):
    cron_m, cron_d = get_previous_date(month, day)

    url = f"https://api.cron-job.org/jobs/{CRON_JOB_ID}"

    headers = {
        "Authorization": f"Bearer {CRON_API_KEY}",
        "Content-Type": "application/json"
    }

    # 👉 帶參數
    cron_url = f"https://linebot-rehab.onrender.com/cron?m={month}&d={day}&h={hour}&mi={minute}"

    data = {
        "job": {
            "enabled": True,
            "url": cron_url,
            "requestMethod": "GET",
            "schedule": {
                "timezone": "Asia/Taipei",
                "hours": [9, 12, 18, 20, 22],
                "minutes": [30],
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
        
    except Exception as e:
        print("cron error:", str(e))
        send_message("❌ cron 更新錯誤")

# ===== 更新 冷cron-job =====
def update_cold_cron(month, day):
    cron_m, cron_d = get_previous_date(month, day)

    url = f"https://api.cron-job.org/jobs/{COLD_CRON_JOB_ID}"

    headers = {
        "Authorization": f"Bearer {CRON_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "job": {
            "enabled": True,
            "requestMethod": 1,
            "schedule": {
                "timezone": "Asia/Taipei",
                "hours": [9, 12, 18, 20, 22],
                "minutes": [25],
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

    # 👉 格式：11/14 14:00
    if " " in text and "/" in text:
        try:
            date_part, time_part = text.split(" ")

            m, d = date_part.split("/")
            hour, minute = time_part.split(":")

            m = int(m)
            d = int(d)
            hour = int(hour)
            minute = int(minute)

            update_cron(m, d, hour, minute)
            update_cold_cron(m, d)

            send_message(f"📅 已設定 {m}/{d}（前一天提醒）")

        except:
            send_message("❌ 格式錯誤，例如：11/14 14:00")

    return "ok"

# ===== cron 觸發 =====
@app.route("/cron")
def cron_job():

    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    
    # 👉 從 URL 拿資料
    try:
        target_m = int(request.args.get("m"))
        target_d = int(request.args.get("d"))
        target_h = int(request.args.get("h"))
        target_min = int(request.args.get("mi"))
    except:
        return "missing params"

    tomorrow = now + datetime.timedelta(days=1)

    # 👉 判斷是否為前一天
    if tomorrow.month == target_m and tomorrow.day == target_d:
        hour = now.hour

        if hour == 9:
            send_message(f"🌅 {target_m}/{target_d} {target_h:02d}:{target_min:02d} 復健")
        elif hour == 12:
            send_message(f"🍱 {target_m}/{target_d} {target_h:02d}:{target_min:02d} 復健")
        elif hour == 18:
            send_message(f"🌆 {target_m}/{target_d} {target_h:02d}:{target_min:02d} 復健")
        elif hour == 20:
            send_message(f"🌙 {target_m}/{target_d} {target_h:02d}:{target_min:02d} 復健")
        elif hour == 22:
            send_message(f"🌙 {target_m}/{target_d} {target_h:02d}:{target_min:02d} 復健")
    
    return "ok"

# ===== health =====
@app.route("/")
def home():
    return "alive", 200
