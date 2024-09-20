from datetime import datetime

from flask import Flask, url_for
from flask import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

counter = {}

from pymongo.mongo_client import MongoClient
from urllib.parse import quote_plus
import os

print(os.getenv('mongodb_username'), os.getenv('mongodb_password'), os.getenv('mongodb_cluster'))

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
    user_collection = db.get_collection('user')
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


# New Routes per user

@app.route("/create_new_user/<username>", methods=['GET'])
def create_new_user(username):
    key = request.args.get('key')
    if key == 'banger':
        user_collection.insert_one({"user": username, "createdat": datetime.now()})
        return f"User: {username} created!"
    return "Oopsie! the request does not bang!"


@app.route("/set_user_key/<username>/<key>", methods=['GET'])
def set_user_key(username, key):
    saved_user = user_collection.find_one({"user": username})
    if not saved_user:
        return "No saved user found"
    user_collection.update_one({"user": username}, {"$set": {"key": key}})
    return "User key set!"


@app.route("/u/<username>", methods=['GET'])
def leaderboard_for_user(username):
    saved_user = user_collection.find_one({"user": username})
    if not saved_user:
        return "No saved user found"
    return render_template("count_per_user.html", key_checked=False)


@app.route("/<username>/key_check", methods=['POST'])
def leaderboard_key_check(username):
    saved_user = user_collection.find_one({"user": username})
    if not saved_user:
        return "No saved user found"
    if saved_user['key'] == key:
        leaderboard_for_user = counter_collection.find({"user": username}).sort([('count', -1)]).limit(20)
        return render_template("count_per_user.html", key_checked=True, leaderboard=leaderboard_for_user)
    return f"Key Mismatch for {username}, you naughty naughty!"


def get_counter_value_for_user(keyword, username):
    counter = counter_collection.find_one({"keyword": keyword, "user": username})
    if counter:
        return counter["count"]
    else:
        counter_collection.insert_one({"keyword": keyword, "count": 0})
        return 0


def increment_counter_for_user(keyword, username):
    old_value = get_counter_value_for_user(keyword, username)
    counter_collection.update_one({"keyword": keyword, "user": username}, {"$set": {"count": old_value + 1}})
    return old_value + 1


def add_stat_for_keyword_for_user(keyword, username):
    stats_collection.insert_one({"keyword": keyword, "date": datetime.now(), "user": username})


@app.route("/u/<username>/count/<keyword>", methods=["POST"])
def count_increment(keyword):
    increment_counter_for_user(keyword)
    add_stat_for_keyword_for_user(keyword)
    return redirect(url_for("count", keyword=keyword), code=302)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
