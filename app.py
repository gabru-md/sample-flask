from flask import Flask, url_for
from flask import render_template
from werkzeug.utils import redirect

app = Flask(__name__)

counter = {}


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/count/<keyword>", methods=["GET"])
def count(keyword):
    return render_template("count.html", keyword=keyword, count=counter.get(keyword, 0))


@app.route("/count/<keyword>", methods=["POST"])
def count_increment(keyword):
    counter[keyword] = counter.get(keyword, 0) + 1
    return redirect(url_for("count", keyword=keyword), code=302)


@app.route("/count", methods=["GET"])
def all_counters():
    return render_template("all_counters.html", counters=counter)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
