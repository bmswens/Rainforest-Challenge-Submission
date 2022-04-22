# built in
import os
from zipfile import ZipFile

# 3rd party
from flask import Blueprint, render_template
from flask import request
from flask import redirect

import logging

# custom
import utils
from database import Database

estimation = Blueprint(
    "estimation",
    __name__,
    "templates"
)

@estimation.route("/")
def leaderboard():
    with Database("db/db.sqlite3") as db:
        top_scores = db.get_top_estimation_scores()
    for index, row in enumerate(top_scores):
        row["rank"] = index + 1
    return render_template("deforestation-estimation-leaderboard.html", ranks=top_scores)

@estimation.route("/submit")
def submission_page():
    return render_template("submit.html")


@estimation.route("/api/submit", methods=["POST"])
def submit():
    team_name = request.form["teamName"]
    emails = request.form["emails"].split('\r\n')
    # just in case
    os.makedirs("submissions/tmp", exist_ok=True)
    os.makedirs(f"submissions/valid/{__name__}", exist_ok=True)
    # the zip file
    zip_path = f"submissions/tmp/{team_name}.zip"
    request.files["submission"].save(zip_path)
    response = utils.verify(zip_path, __name__)
    if not response["ok"]:
        return response
    # make the folder to extract to
    utils.save(zip_path, __name__, team_name, emails)
    return redirect("/estimation/", code=301)

@estimation.route('/api/expected-files')
def get_expected_files():
    f_type = ".png"
    files = utils.get_files("/app/truth/estimation", f_type)
    return {
        "count": len(files),
        "image_type": f_type,
        "files": files
    }