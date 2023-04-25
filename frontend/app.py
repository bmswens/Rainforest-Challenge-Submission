# 3rd party 
from flask import Flask, render_template

# custom
from fire import fire
from estimation import estimation
from translation import translation

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

app.register_blueprint(fire, url_prefix="/fire")
app.register_blueprint(estimation, url_prefix="/deforestation")
app.register_blueprint(translation, url_prefix="/translation")