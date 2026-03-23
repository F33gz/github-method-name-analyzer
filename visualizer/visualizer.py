import os
import threading
import time
from collections import Counter
from flask import Flask, render_template, jsonify, request
import redis

app = Flask(__name__)
redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)

word_counter = Counter()

def background_redis_reader():
    while True:
        try:
            result = redis_client.brpop("method_words", timeout=5)
            if result:
                _, word = result
                word_counter[word] += 1
        except redis.ConnectionError:
            time.sleep(2)
        except Exception:
            time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        limit = 20
        
    top_words = word_counter.most_common(limit)
    labels = [item[0] for item in top_words]
    data = [item[1] for item in top_words]
    return jsonify({
        "labels": labels,
        "data": data,
        "total": sum(word_counter.values())
    })

if __name__ == "__main__":
    time.sleep(5)
    t = threading.Thread(target=background_redis_reader, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
