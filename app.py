from flask import Flask, render_template
from flask.json import JSONEncoder
from datetime import datetime

app = Flask(__name__)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__, template_folder="templates", static_folder="templates/static")
app.json_encoder = CustomJSONEncoder
app.secret_key = "secret"


@app.route("/ping")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/")
def home_page():
    return render_template("home.html")

@app.route("/eat_now")
def eat_now():
    return render_template("eat_now.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5034, threaded=True)

