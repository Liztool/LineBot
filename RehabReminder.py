from flask import Flask, request, abort
import requests
import datetime
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "pQNfJtvwbb5dRup2oyJKo+3gjd3b3mqJFAfuBq5f8fM/uStUOlFDpQHMIR+fP8nOTTkD8c2xlwirYwWx8+izapE4CB5oeugrHtfqTyGruF6lMWkYvxt4yWf4HL7mBeBhdohu57ragbZ03GERuXkN2QdB04t89/1O/w1cDnyilFU="
USER_ID = "U151594c7fb7d826fd8fba8261e7164ed"

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

# 👉 自訂：每月哪一天
TARGET_DAY = 25

@app.route("/cron")
def cron_job():
    now = datetime.datetime.now()

    tomorrow = now + datetime.timedelta(days=1)

    # 如果明天是目標日
    if tomorrow.day == TARGET_DAY:
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