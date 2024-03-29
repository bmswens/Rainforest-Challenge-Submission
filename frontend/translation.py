# built in
import os
from zipfile import ZipFile
import json

# 3rd party
from flask import Blueprint, render_template
from flask import request
from flask import redirect

import logging

# custom
import utils
from database import Database

translation = Blueprint(
    "translation",
    __name__,
    "templates"
)

@translation.route("/")
def leaderboard():
    with Database("db/db.sqlite3") as db:
        # top scores hidden
        top_scores = db.get_top_translation_scores()
    for index, row in enumerate(top_scores):
        row["rank"] = index + 1
    return render_template("image-translation-leaderboard.html", ranks=top_scores)

@translation.route("/submit")
def submission_page():
    return render_template("submit.html")


@translation.route("/api/submit", methods=["POST"])
def submit():
    team_name = request.form["teamName"]
    emails = request.form["emails"].split('\r\n')
    # just in case
    os.makedirs("submissions/tmp", exist_ok=True)
    os.makedirs(f"submissions/valid/{__name__}", exist_ok=True)
    # the zip file
    zip_path = f"submissions/tmp/{team_name}.zip"
    request.files["submission"].save(zip_path)
    response = utils.verify_c3(zip_path, translation)
    if not response["ok"]:
        return response
    # make the folder to extract to
    utils.save(zip_path, __name__, team_name, emails)
    return redirect("/translation/", code=301)

@translation.route('/api/expected-files')
def get_expected_files():
    f_type = ".tiff"
    with open('/app/truth/translation/files.json') as incoming:
        items = json.load(incoming)
    files = []
    for key in items:
        for f in eval(key):
            files.append(os.path.join('/translation', f))
    return {
        "count": len(files),
        "image_type": f_type,
        "files": files
    }
