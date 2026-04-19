from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "ok"

@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.json
    print(data)
    return "ok"

if __name__ == "__main__":
    app.run()