# built in
import os
import json
import time

# 3rd party
import torch
import torchvision.transforms as transforms
import PIL
import lpips
from schedule import every, repeat, run_pending

# custom
from database import Database

# torch setups
GPU = torch.cuda.is_available()
toTensor = transforms.ToTensor()

# lpips setup
lpips_fn = lpips.LPIPS(net='alex')

# logging
import logging
logging.basicConfig(
    filename="eval.log", 
    format=f"[%(asctime)s] [%(levelname)s] [{__file__}] %(message)s", 
    level=logging.INFO, 
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)

def path_to_tensor(path):
    image = PIL.Image.open(path).convert("RGB")
    tensor = toTensor(image)
    if GPU:
        tensor = tensor.cuda()
    return tensor


def eval_single_folder(submission, truth):
    output = {
        "min": 1
    }
    values = []
    input_files = [f for f in os.listdir(submission) if '.png' in f]
    truth_files = [f for f in os.listdir(truth) if '.png' in f]
    for submitted in input_files:
        submitted_path = os.path.join(submission, submitted)
        submitted_tensor = path_to_tensor(submitted_path)
        for truth_f in truth_files:
            truth_path = os.path.join(truth, truth_f)
            truth_tensor = path_to_tensor(truth_path)
            lpips_response = lpips_fn(submitted_tensor, truth_tensor)
            score = lpips_response.item()
            output[f"{submitted.replace('.png', '')} -> {truth_f.replace('.png', '')}"] = score
            values.append(score)
    output["min"] = min(values)
    return output


def eval_submission(submission, truth="/app/truth/translation"):
    output = {
        "average": 1
    }
    total = []
    to_evaluate = []
    for item in os.listdir(truth):
        full_path = os.path.join(truth, item)
        if os.path.isdir(full_path):
            to_evaluate.append(full_path)
    for folder in to_evaluate:
        input_image = os.path.basename(folder)
        submission_folder = os.path.join(submission, "images", input_image)
        scores = eval_single_folder(submission_folder, folder)
        output[input_image] = scores
        total.append(scores["min"])
        logging.info(f"{input_image} {scores['min']}")
    if total:
        output["average"] = sum(total) / len(total)
    return output


def eval_team(folder):
    team = os.path.basename(folder)
    logging.info(f"Eval Team: {team}")
    scores = []
    submission = os.listdir(folder)
    for submission in submission:
        meta_path = os.path.join(folder, submission, "metadata.json")
        with open(meta_path) as incoming:
            metadata = json.load(incoming)
        if metadata["evaluated"]:
            continue
        logging.info(f"Eval {submission}")
        submission_path = os.path.join(folder, submission)
        score = eval_submission(submission_path)
        metadata['scores'] = score
        with open(meta_path, 'w') as output:
            output.write(json.dumps(metadata, indent=2))
        logging.info(f"Average: {score['average']}")
        scores.append(score['average'])
    this_best = min(scores)
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


if __name__ == "__main__":
    while True:
        run_pending()
        time.sleep(1)