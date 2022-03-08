# built in
import os
import random
import json
import time

# 3rd party
from schedule import every, repeat, run_pending

# custom
from database import Database

# logging
import logging
logging.basicConfig(
    filename="eval.log", 
    format="[%(asctime)s] [%(levelname)s] %(message)s", 
    encoding="utf-8", 
    level=logging.INFO, 
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)


def evaluate(path):
    """
    Actual implementation goes here.
    PSNR
    LPIPS
    SSIM
    """
    return random.randint(0, 100)
   

def eval_team(team_path, team):
    scores = []
    items = [os.path.join(team_path, item) for item in os.listdir(team_path)]
    folders = [f for f in items if os.path.isdir(f)]
    for folder in folders:
        meta_path = os.path.join(team_path, folder, "metadata.json")
        image_path = os.path.join(team_path, folder, "images")
        with open(meta_path) as incoming:
            metadata = json.load(incoming)
        if metadata["evaluated"]:
            continue
        logging.info(f"New submission for team: {team}; folder: {folder}")
        score = evaluate(image_path)
        logging.info(f"Score: {score}")
        metadata["evaluated"] = True
        metadata["score"] = score
        with open(meta_path, 'w') as output:
            content = json.dumps(metadata, indent=2)
            output.write(content)
        scores.append(score)
    return scores
        
@repeat(every(30).seconds)
def main(path="/app/submissions/valid"):
    logging.info("Starting scan")
    items = [os.path.join(path, item) for item in os.listdir(path)]
    folders = [f for f in items if os.path.isdir(f)]
    for folder in folders:
        team = os.path.split(folder)[1]
        logging.info(f"Evaluating team: {team}")
        scores = eval_team(folder, team)
        if not scores:
            continue
        top_score = max(scores)
        with Database("db/db.sqlite3") as db:
            previous_max = db.get_score_by_team(team)
            print(top_score, previous_max)
            if top_score > previous_max:
                db.query(f"UPDATE scores SET score = {top_score} WHERE team = '{team}'")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)