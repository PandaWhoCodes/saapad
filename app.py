from os import environ as env
from flask import Flask, render_template, session, url_for, redirect
from flask.json import JSONEncoder
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
import requests

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
oauth = OAuth(app)

ENV_FILE = find_dotenv()
PROFILE_KEY = env.get("user", "user")
JWT_PAYLOAD = env.get("jwt-payload", "JWT_PAYLOAD")
if ENV_FILE:
    load_dotenv(ENV_FILE)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email",},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


@app.route("/ping")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/")
def home_page():
    print(session)
    if PROFILE_KEY not in session:
        return redirect("/login")
    return render_template("home.html")


@app.route("/eat_now")
def eat_now():
    return render_template("eat_now.html")


# Auth part - https://realpython.com/flask-google-login


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    # session["user"] = token
    headers = {
        "Authorization": f'Bearer {token["access_token"]}',
        "Content-Type": "application/json",
    }

    response = requests.get(
        f'https://{env.get("AUTH0_DOMAIN")}/userinfo', headers=headers
    )
    resp = response.json()
    token["email"] = resp["email"]
    session[JWT_PAYLOAD] = resp
    session[PROFILE_KEY] = token
    return redirect("/")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5034, threaded=True)

