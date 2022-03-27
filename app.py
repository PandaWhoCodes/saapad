from os import environ as env
from flask import Flask, render_template, session, url_for, redirect
from flask.json import JSONEncoder
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
import requests
from urllib.parse import quote_plus, urlencode

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
COMPANY_DOMAIN = env.get("company_domain")
MAX_MEALS_PER_DAY = int(env.get("MAX_MEALS_PER_DAY", 1))

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
    if PROFILE_KEY not in session:
        return redirect("/login")
    return render_template("home.html")


@app.route("/eat_now")
def eat_now():
    if PROFILE_KEY not in session:
        return redirect("/login")
    if not session[PROFILE_KEY]["email"].endswith(COMPANY_DOMAIN):
        return render_template("you_are_out.html")

    if "last_eat_date" in session:
        last_meal_day = datetime.strptime(
            session["last_eat_date"], "%Y-%m-%d %H:%M:%S.%f"
        )
        if last_meal_day.date() == datetime.now().date():
            if session["todays_meals"] >= MAX_MEALS_PER_DAY:
                return redirect("/out")
            else:
                session["todays_meals"] = int(session["todays_meals"]) + 1
    else:
        session["last_eat_date"] = str(datetime.now())
        session["todays_meals"] = 1
    # print(session)
    day = datetime.now().strftime("%A")
    time = datetime.now().strftime("%H:%M %p")
    return render_template("eat_now.html", day=day, time=time)


@app.route("/out")
def out():
    return render_template("you_are_out.html")


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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home_page", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5034, threaded=True)

