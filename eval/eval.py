# built in
import os
import json
import time

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

def mse(imageA, imageB):
	err = numpy.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	return err

def evaluate(path):
    """
    Actual implementation goes here.
    PSNR -- cv2; switched to MSE because I don't know how to use PSNR otherwise
    LPIPS -- pip installed
    SSIM -- scikit-image
    """
    gpu = torch.cuda.is_available()
    truth_folder = "/app/truth/images"
    # eval functions
    lpips_fn = lpips.LPIPS(net='alex')
    if gpu:
        lpips_fn.cuda()
    scores = []
    for f in os.listdir(truth_folder):
        # truth
        truth_path = os.path.join(truth_folder, f)
        truth_im = PIL.Image.open(truth_path).convert("RGB")
        truth_array = numpy.array(truth_im)
        truth_cv = cv2.imread(truth_path)
        truth_tensor = toTensor(truth_im)
        if gpu:
            truth_tensor.cuda()
        # submission
        submission_path = os.path.join(path, f)
        submission_im = PIL.Image.open(submission_path).convert("RGB")
        submission_array = numpy.array(submission_im)
        submission_cv = cv2.imread(submission_path)
        submission_tensor = toTensor(submission_im)
        if gpu:
            submission_tensor.cuda()
        # scores
        score_lpips = lpips_fn.forward(submission_tensor, truth_tensor)
        score_lpips = 1 - score_lpips.item() # inverts it so that 1 is better
        score_ssim = SSIM(submission_array, truth_array, multichannel=True)
        score_mse = 1 - mse(submission_cv, truth_cv)
        scores.append((score_lpips + score_mse + score_ssim) / 3)
    return (sum(scores) / len(scores)) * 100
   

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
        
@repeat(every(60).seconds)
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
    logging.info("Done with scan")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)