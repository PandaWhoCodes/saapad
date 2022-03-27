from flask import Flask

app = Flask(__name__)


@app.route("/ping")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5034, threaded=True)

