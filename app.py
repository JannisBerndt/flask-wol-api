import os
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Preset
from wol import bp

app.register_blueprint(bp)

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/docs/')
def docs():
    return render_template('swaggerui.html')


if __name__ == '__main__':
    app.run()
