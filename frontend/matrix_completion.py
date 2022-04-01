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

matrix_completion = Blueprint(
    "matrix_completion",
    __name__,
    "templates"
)

@matrix_completion.route("/")
def leaderboard():
    with Database("db/db.sqlite3") as db:
        top_scores = db.get_top_scores("MatrixCompletionScores")
    for index, row in enumerate(top_scores):
        row["rank"] = index + 1
    return render_template("matrix-completion-leaderboard.html", ranks=top_scores)

@matrix_completion.route("/submit")
def submission_page():
    return render_template("submit.html")


@matrix_completion.route("/api/submit", methods=["POST"])
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
    return redirect("/matrix-completion/", code=301)