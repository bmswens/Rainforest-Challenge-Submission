# built in
import os
from zipfile import ZipFile
import json
import datetime

# 3rd party 
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

import logging

# custom
import verify
import config
from database import Database

app = Flask(__name__)

@app.route("/")
def leaderboard():
    with Database("db/db.sqlite3") as db:
        top_scores = db.get_top_scores()
    ranks = [{"rank": index + 1, "name": row["team"], "score": row["score"]} for index, row in enumerate(top_scores)]
    return render_template("leaderboard.html", ranks=ranks)

@app.route("/submit")
def submission_page():
    return render_template("submit.html")


@app.route("/api/submit", methods=["POST"])
def submit():
    team_name = request.form["teamName"]
    emails = request.form["emails"].split('\r\n')
    now = datetime.datetime.now()
    # just in case
    os.makedirs("submissions/tmp", exist_ok=True)
    os.makedirs("submissions/valid", exist_ok=True)
    # the zip file
    zip_path = f"submissions/tmp/{team_name}.zip"
    request.files["submission"].save(zip_path)
    response = verify.contents(zip_path)
    if not response["ok"]:
        return response
    # make the folder to extract to
    team_folder = f"submissions/valid/{team_name}/{now.isoformat().replace(':', '-')}"
    image_target = f"{team_folder}/images"
    os.makedirs(image_target, exist_ok=True)
    with ZipFile(zip_path) as archive:
        files = archive.namelist()
        to_extract = [f for f in files if config.image_type in f]
        archive.extractall(image_target, to_extract)
    with open(f"{team_folder}/metadata.json", 'w') as output:
        content = json.dumps(
            {
                "team": team_name,
                "emails": emails,
                "timestamp": now.isoformat(),
                "evaluated": False
            },
            indent=2
        )
        output.write(content)
    os.remove(zip_path)
    return redirect("/", code=301)