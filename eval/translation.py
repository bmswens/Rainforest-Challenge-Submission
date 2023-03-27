# built in
import json
import os
import time

# 3rd party
import rasterio
from sklearn.metrics import mean_squared_error as MSE
import numpy as np
from schedule import every, repeat, run_pending

# custom
from database import Database

# logging
import logging
logging.basicConfig(
    filename="eval.log",
    format=f"[%(asctime)s] [%(levelname)s] [{__file__}] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)

def avg(x):
    if not x:
        return 1000
    return sum(x) / len(x)

def norm_image(z):
    immax = np.max(z)
    immin = np.min(z)
    divisor = immax - immin
    if not divisor:
        divisor = 1.0
    norm_z = (z-immin)/(divisor)
    norm_z = norm_z.astype(np.float64)
    return norm_z


def load_image(path):
    img = rasterio.open(path).read()
    if img.shape[2] == 3:
        img = img.transpose(2, 0, 1)
    elif img.shape[0] != 3:
        logging.error(f"Shape is {img.shape}")
    multi_rgb = np.zeros((3,256,256))
    multi_rgb[0,:,:] = norm_image(img[0])
    multi_rgb[1,:,:] = norm_image(img[1])
    multi_rgb[2,:,:] = norm_image(img[2])
    return multi_rgb


def eval_mapping(obj, submission_folder, truth="/app/truth/translation"):
    output = {}
    values = []
    for truth_path in obj:
        MSEs = []
        truth_abs_path = os.path.join(truth, truth_path)
        truth_img = load_image(truth_abs_path)
        output[truth_path] = {}
        for submission_path in obj[truth_path]:
            submission_abs_path = os.path.join(submission_folder, 'images', submission_path)
            submission_img = load_image(submission_abs_path)
            mse = MSE(truth_img.flatten(), submission_img.flatten())
            MSEs.append(mse)
            output[truth_path][submission_path] = mse
            logging.info(f"{truth_path.replace('.tiff', '')} -> {submission_path.replace('.tiff', '')} = {mse}")
        best = min(MSEs)
        output[truth_path]["min"] = best
        values.append(best)
    output["sum"] = sum(values)
    return output


def eval_submission(submission, truth="/app/truth/translation"):
    output = {}
    values = []
    with open(os.path.join(truth, 'mappings.json')) as incoming:
        inputs = json.load(incoming)
    for input_f in inputs:
        mapping = inputs[input_f]
        scores = eval_mapping(mapping, submission)
        output[input_f] = scores
        values.append(scores["sum"])
    output["average"] = avg(values)
    return output


def eval_team(folder):
    team = os.path.basename(folder)
    logging.info(f"Eval Team: {team}")
    scores = []
    submission = os.listdir(folder)
    for submission in submission:
        meta_path = os.path.join(folder, submission, "metadata.json")
        metadata = {
                "team": team,
                "emails": [],
                "timestamp": "",
                "evaluated": False
            }
        try:
            with open(meta_path) as incoming:
                metadata = json.load(incoming)
        except:
            pass
        if metadata["evaluated"]:
            continue
        logging.info(f"Eval {submission}")
        submission_path = os.path.join(folder, submission)
        try:
            score = eval_submission(submission_path)
        except Exception as e:
            logging.error(f'{e}')
            continue
        metadata['score'] = score
        metadata['evaluated'] = True
        with open(meta_path, 'w') as output:
            output.write(json.dumps(metadata, indent=2))
        logging.info(f"Average: {score['average']}")
        scores.append(score['average'])
    if not scores:
        return
    this_best = min(scores, default=1000)
    with Database("db/db.sqlite3") as db:
        previous_best = db.get_translation_score_by_team(team)
        if this_best < previous_best:
            db.query(f"UPDATE ImageToImageScores SET score = {this_best} WHERE team = '{team}'")


@repeat(every(60).seconds)
def main(path="/app/submissions/valid/translation"):
    os.makedirs(path, exist_ok=True)
    logging.info("Starting scan")
    items = [os.path.join(path, item) for item in os.listdir(path)]
    teams = [f for f in items if os.path.isdir(f)]
    for team in teams:
        eval_team(team)
    logging.info("Done with scan")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)

