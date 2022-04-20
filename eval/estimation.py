# built in
from multiprocessing.sharedctypes import Value
import os
import json
import time
import sys

# 3rd party
from schedule import every, repeat, run_pending
from PIL import Image
from sklearn.metrics import f1_score
import numpy as np
from sklearn.preprocessing import normalize

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

def get_pixel_accuracy(truth, submission):
    pixels = []
    for x in range(truth.width):
        for y in range(truth.height):
            coordinates = (x, y)
            true_pixel = truth.getpixel(coordinates)
            pred_pixel = submission.getpixel(coordinates)
            if true_pixel == pred_pixel:
                pixels.append(1)
            else:
                pixels.append(0)
    accuracy = sum(pixels) / len(pixels)
    accuracy = accuracy * 100
    return accuracy

def get_f1_score(truth, submission, chip):
    truth = np.array(truth)
    truth = truth.flatten()
    submission = np.array(submission)
    submission = submission.flatten()
    logging.info(chip)
    score = 0
    try:
        score = f1_score(truth, submission, zero_division=1, pos_label=0)
    except:
        logging.info(np.unique(truth))
        logging.info(np.unique(submission))
        raise ValueError("oops")
    return score


def get_iou(truth, submission, target=0):
    total_areas = 0
    correct = 0
    truth = np.array(truth)
    truth = truth.flatten()
    submission = np.array(submission)
    submission = submission.flatten()
    for index, true_pixel in enumerate(truth):
        if true_pixel == target:
            total_areas += 1
        pred_pixel = submission[index]
        if true_pixel == target and pred_pixel == target:
            correct += 1
    if not total_areas:
        return 0
    else:
        return correct / total_areas


def eval_date(submission_folder, truth_folder):
    output = {}
    chips = [f for f in os.listdir(truth_folder) if '.png' in f]
    for chip in chips:
        # truth
        truth_path = os.path.join(truth_folder, chip)
        truth_image = Image.open(truth_path).convert('L')

        # submission
        submission_path = os.path.join(submission_folder, chip)
        submission_image = Image.open(submission_path).convert('L')

        # pixel accuracy
        accuracy = get_pixel_accuracy(truth_image, submission_image)
        f1 = get_f1_score(truth_image, submission_image, chip)
        iou = get_iou(truth_image, submission_image)

        scores = {
            "accuracy": accuracy,
            "f1": f1,
            "iou": iou
        }

        logging.info(scores)
        output[chip] = scores
    # get averages
    accuracies = [v["accuracy"] for v in output.values()]
    f1s = [v["f1"] for v in output.values()]
    ious = [v["iou"] for v in output.values()]
    if accuracies:
        output["accuracy"] = sum(accuracies) / len(accuracies)
    if f1s:
        output["f1"] = sum(accuracies) / len(accuracies)
    if ious:
        output["iou"] = sum(ious) / len(ious)
    return output

def eval_submission(folder):
    output = {}

    # skipped if evaluated
    meta_path = os.path.join(folder, 'metadata.json')
    with open(meta_path) as incoming:
        meta = json.load(incoming)
    if meta["evaluated"]:
        return output
    # log
    final = os.path.basename(folder)
    logging.info(f"Evaluating {final}")

    truth_folder = "/app/truth/estimation"
    dates = os.listdir(truth_folder)
    # averages
    accuracies = []
    f1s = []
    ious = []
    for date in dates:
        truth_path = os.path.join(truth_folder, date)
        submission_path = os.path.join(folder, 'images', date)
        logging.info(f'Evaluating date: {date}')
        scores = eval_date(submission_path, truth_path)
        output[date] = scores
        accuracies.append(scores["accuracy"])
        f1s.append(scores["f1"])
        ious.append(scores["iou"])
    if accuracies:
        output["accuracy"] = sum(accuracies) / len(accuracies)
    else:
        output["accuracy"] = 0
    if f1s:
        output["f1"] = sum(accuracies) / len(accuracies)
    else:
        output["f1"] = 0
    if ious:
        output["iou"] = sum(ious) / len(ious)
    else:
        output["iou"] = 0
    # write out meta data
    meta['scores'] = output
    meta['evaluated'] = True
    with open(meta_path, 'w') as outgoing:
        outgoing.write(json.dumps(meta, indent=2))
    return output


def eval_team(folder, team):
    submissions = [f for f in os.listdir(folder)]
    accuracy = 0
    best = {}
    logging.info(submissions)
    for submission in submissions:
        full_path = os.path.join(folder, submission)
        scores = eval_submission(full_path)
        logging.info(f"Accuracy: {scores['accuracy']} F1: {scores['f1']} IOU: {scores['iou']}")
        if scores["accuracy"] > accuracy:
            best = scores
            accuracy = scores["accuracy"]
        with Database('db/db.sqlite3') as db:
            previous_best = db.get_estimation_score_by_team(team)
            if accuracy > previous_best:
                db.query(f"UPDATE EstimationScores SET pixel = {accuracy}, f1 = {best['f1']}, iou = {best['iou']} WHERE team = '{team}'")

        
@repeat(every(60).seconds)
def main(path="/app/submissions/valid/estimation"):
    os.makedirs(path, exist_ok=True)
    logging.info("Starting scan")
    items = [os.path.join(path, item) for item in os.listdir(path)]
    folders = [f for f in items if os.path.isdir(f)]
    for folder in folders:
        team = os.path.split(folder)[1]
        logging.info(f"Evaluating team: {team}")
        eval_team(folder, team)    
    logging.info("Done with scan")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)
