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
from pytorch_fid import fid_score
import subprocess
import rasterio

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

toTensor = transforms.ToTensor()
np = numpy

# monkey patch
from pytorch_fid.fid_score import ImagePathDataset

def monkey_patch_get_item(self, i):
    path = self.files[i]
    img = rasterio.open(path).read()[0]
    img = norm_image(img).astype(numpy.float32)
    img = numpy.dstack([img, img, img])
    if self.transforms is not None:
        img = self.transforms(img)
    return img

ImagePathDataset.__getitem__ = monkey_patch_get_item


def get_averages(scores):
    if not scores:
        scores["lpips"] = 1
        scores["ssim"] = 0
        scores["psnr"] = 0
        scores["fid"] = 1
        return scores
    lpips_scores = [v["lpips"] for v in scores.values()]
    ssim_scores = [v["ssim"] for v in scores.values()]
    psnr_scores = [v["psnr"] for v in scores.values()]
    fid_scores = [v.get('fid', 1) for v in scores.values()]
    scores["lpips"] = sum(lpips_scores) / len(lpips_scores)
    scores["ssim"] = sum(ssim_scores) / len(ssim_scores)
    scores["psnr"] = sum(psnr_scores) / len(psnr_scores)
    scores["fid"] = sum(fid_scores) / len(fid_scores)
    return scores

def norm_image(z):
    immax = np.max(z)
    immin = np.min(z)
    divisor = immax - immin
    if not divisor:
        divisor = 1
    norm_z = (z-immin)/(divisor)
    norm_z = norm_z.astype(np.float64)
    return norm_z


def rasterio_to_tensor(img):
    divisor = np.amax(img) - np.amin(img)
    if not divisor:
        divisor = 1
    normalized_input = (img - np.amin(img)) / (divisor)
    normalized_input = 2*normalized_input - 1
    stack = np.dstack((normalized_input, normalized_input, normalized_input))
    stack = stack.reshape([1,3,stack.shape[0],stack.shape[0]])
    tensor = torch.Tensor(stack)
    return tensor

def eval_folder(truth_folder, submission_folder, lpips_fn, gpu):
    logging.info(f"Evaluating {truth_folder} folder")
    scores = {}
    lpips_scores = []
    for f in os.listdir(truth_folder):
        # truth
        truth_path = os.path.join(truth_folder, f)
        truth_im = rasterio.open(truth_path).read()[0]
        truth_im = norm_image(truth_im)
        truth_tensor = rasterio_to_tensor(truth_im)
        if gpu:
           truth_tensor.cuda()
            # submission
        submission_path = os.path.join(submission_folder, f)
        submission_im = rasterio.open(submission_path).read()[0]
        submission_im = norm_image(submission_im)
        submission_tensor = rasterio_to_tensor(submission_im)
        if gpu:
            submission_tensor.cuda()
            # scores
        # debug
        score_lpips = lpips_fn.forward(submission_tensor, truth_tensor)
        score_lpips = score_lpips.item()
        score_ssim = SSIM(submission_im, truth_im)

        score_psnr = cv2.PSNR(truth_im, submission_im)
        if numpy.isnan(score_psnr):
            logging.error(truth_im)
            logging.error(submission_im)
        scores[f] = {
                "lpips": score_lpips,
                "ssim": score_ssim,
                "psnr": score_psnr
            }
        lpips_scores.append(score_lpips)
    scores = get_averages(scores)
    return scores

def evaluate(path):
    """
    Actual implementation goes here.
    PSNR -- cv2; 
    LPIPS -- pip installed
    SSIM -- scikit-image
    """
    gpu = torch.cuda.is_available()
    device = 'cuda' if gpu else 'cpu'
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
        # results = {"psnr": 360, "lpips": 0, "ssim": 1}
        # TODO: Replace this hack with the actual Python function call
        try:
            results["fid"] = fid_score.calculate_fid_given_paths(
                [mode_folder, submission_folder],
                1,
                device,
                2048
            )
        except Exception as e:
            logging.error(e)
            results["fid"] = 1
        logging.info(f"FID: {results['fid']}")
        #results["fid"] = float(subprocess.check_output(f"python3 -m pytorch_fid --num-workers 1 {submission_folder} {mode_folder}", shell=True).replace('FID: ', '').replace("\n", '')) # fid_score.calculate_fid_given_paths([submission_folder, truth_folder], 1, device, 2048, 2)
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
        logging.info(f"Scores: LPIPS: {results['lpips']} SSIM: {results['ssim']} PSNR: {results['psnr']} FID: {results['fid']}")
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
                db.query(f"UPDATE MatrixCompletionScores SET lpips = {best_score}, psnr = {low_score['psnr']}, ssim = {low_score['ssim']}, fid = {low_score['fid']} WHERE team = '{team}'")
    logging.info("Done with scan")


if __name__ == '__main__':
    while True:
        run_pending()
        time.sleep(1)
