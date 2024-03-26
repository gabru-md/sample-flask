from datetime import datetime

from flask import Flask, url_for
from flask import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

counter = {}

from pymongo.mongo_client import MongoClient
from urllib.parse import quote_plus
import os

username = quote_plus(os.getenv('mongodb_username'))
password = quote_plus(os.getenv('mongodb_password'))
cluster = os.getenv('mongodb_cluster')

uri = 'mongodb+srv://' + username + ':' + password + '@' + cluster + '/?retryWrites=true&w=majority&appName=Auto-Skribbl-Cluster'

client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    db = client.get_database('counter')
    counter_collection = db.get_collection('counter')
    stats_collection = db.get_collection('stats')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


def get_counter_value(keyword):
    counter = counter_collection.find_one({"keyword": keyword})
    if counter:
        return counter["count"]
    else:
        counter_collection.insert_one({"keyword": keyword, "count": 0})
        return 0


def increment_counter(keyword):
    old_value = get_counter_value(keyword)
    counter_collection.update_one({"keyword": keyword}, {"$set": {"count": old_value + 1}})
    return old_value + 1


def add_stat_for_keyword(keyword):
    stats_collection.insert_one({"keyword": keyword, "date": datetime.now()})


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/count/<keyword>", methods=["GET"])
def count(keyword):
    counter_value = get_counter_value(keyword)
    return render_template("count.html", keyword=keyword, count=counter_value)


@app.route("/count/<keyword>", methods=["POST"])
def count_increment(keyword):
    increment_counter(keyword)
    add_stat_for_keyword(keyword)
    return redirect(url_for("count", keyword=keyword), code=302)


@app.route("/count", methods=["GET"])
def all_counters():
    leaderboard = counter_collection.find().sort([('count', -1)]).limit(20)
    return render_template("all_counters.html", counters=leaderboard)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
