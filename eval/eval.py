# built in
import os
import json
import time
import sys

# 3rd party
from schedule import every, repeat, run_pending
import lpips
import cv2
from skimage.metrics import structural_similarity as SSIM
import torchvision.transforms as transforms
import torch
import PIL
import numpy

# custom
from database import Database

# logging
import logging
logging.basicConfig(
    filename="eval.log", 
    format="[%(asctime)s] [%(levelname)s] %(message)s", 
    level=logging.INFO, 
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)

toTensor = transforms.ToTensor()

def get_averages(scores):
    if not scores:
        scores["lpips"] = 1
        scores["ssim"] = 0
        scores["psnr"] = 0
        return scores
    lpips_scores = [v["lpips"] for v in scores.values()]
    ssim_scores = [v["ssim"] for v in scores.values()]
    psnr_scores = [v["psnr"] for v in scores.values()]
    scores["lpips"] = sum(lpips_scores) / len(lpips_scores)
    scores["ssim"] = sum(ssim_scores) / len(ssim_scores)
    scores["psnr"] = sum(psnr_scores) / len(psnr_scores)
    return scores

def eval_folder(truth_folder, submission_folder, lpips_fn, gpu):
    logging.info(f"Evaluating {truth_folder} folder")
    scores = {}
    lpips_scores = []
    for f in os.listdir(truth_folder):
        # truth
        truth_path = os.path.join(truth_folder, f)
        try:
            truth_im = PIL.Image.open(truth_path).convert("RGB")
            truth_array = numpy.array(truth_im)
            truth_cv = cv2.imread(truth_path)
            truth_tensor = toTensor(truth_im)
            if gpu:
                truth_tensor.cuda()
            # submission
            submission_path = os.path.join(submission_folder, f)
            submission_im = PIL.Image.open(submission_path).convert("RGB")
            submission_array = numpy.array(submission_im)
            submission_cv = cv2.imread(submission_path)
            submission_tensor = toTensor(submission_im)
            if gpu:
                submission_tensor.cuda()
            # scores
            score_lpips = lpips_fn.forward(submission_tensor, truth_tensor)
            score_lpips = score_lpips.item()
            score_ssim = SSIM(submission_array, truth_array, multichannel=True)
            score_psnr = cv2.PSNR(truth_cv, submission_cv)
            scores[f] = {
                "lpips": score_lpips,
                "ssim": score_ssim,
                "psnr": score_psnr
            }
            lpips_scores.append(score_lpips)
        except:
            e = sys.exc_info()[0]
            logging.error(f"Failed to analyze {truth_path}")
            logging.error(str(e))
    scores = get_averages(scores)
    return scores

def evaluate(path):
    """
    Actual implementation goes here.
    PSNR -- cv2; switched to MSE because I don't know how to use PSNR otherwise
    LPIPS -- pip installed
    SSIM -- scikit-image
    """
    gpu = torch.cuda.is_available()
    truth_folder = "/app/truth/matrix-completion"
    # eval functions
    lpips_fn = lpips.LPIPS(net='alex')
    if gpu:
        lpips_fn.cuda()
    scores = {}
    for folder in os.listdir(truth_folder):
        mode_folder = os.path.join(truth_folder, folder)
        if not os.path.isdir(mode_folder):
            continue
        submission_folder = os.path.join(path, folder)
        results = eval_folder(mode_folder, submission_folder, lpips_fn, gpu)
        scores[folder] = results
    scores = get_averages(scores)
    return scores
   

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
        results = evaluate(image_path)
        logging.info(f"Scores: LPIPS: {results['lpips']} SSIM: {results['ssim']} PSNR: {results['psnr']}")
        metadata["evaluated"] = True
        metadata.update(**results)
        with open(meta_path, 'w') as output:
            content = json.dumps(metadata, indent=2)
            output.write(content)
        scores.append(results)
    return scores
        
@repeat(every(60).seconds)
def main(path="/app/submissions/valid/matrix_completion"):
    os.makedirs(path, exist_ok=True)
    logging.info("Starting scan")
    items = [os.path.join(path, item) for item in os.listdir(path)]
    folders = [f for f in items if os.path.isdir(f)]
    for folder in folders:
        team = os.path.split(folder)[1]
        logging.info(f"Evaluating team: {team}")
        scores = eval_team(folder, team)
        if not scores:
            continue
        low_score = scores[0]
        for score in scores:
            if score["lpips"] < low_score["lpips"]:
                low_score = score
        best_score = low_score["lpips"]
        with Database("db/db.sqlite3") as db:
            logging.info(team)
            previous_best = db.get_completion_score_by_team(team)
            logging.info(f"Previous Best: {previous_best} This Best: {best_score}")
            if best_score < previous_best:
                db.query(f"UPDATE MatrixCompletionScores SET lpips = {best_score}, psnr = {low_score['psnr']}, ssim = {low_score['ssim']} WHERE team = ?", [team])
    logging.info("Done with scan")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)