#!python3
# built in

# 3rd party
import lpips
import cv2
from skimage.metrics import structural_similarity as SSIM
from pytorch_fid import fid_score
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from pytorch_fid import fid_score

# lpips setup
lpips_fn = lpips.LPIPS(net='alex')

# PyTorch setup
toTensor = transforms.ToTensor()

# Matrix Functions

def eval_lpips(generated_image, truth_image):
    """
    Takes in two paths and returns the LPIPS score.
    Inputs:
        generated_image: String; path to generated image
        truth_image: String; path to truth image
        use_gpu: Boolean; push tensors to GPU
    Outputs:
        score: float; LPIPS score
    """
    generated_image = Image.open(generated_image).convert('RGB')
    generated_tensor = toTensor(generated_image)

    truth_image = Image.open(truth_image).convert("RGB")
    truth_tensor = toTensor(truth_image)

    lpips_tensor = lpips_fn.forward(generated_tensor, truth_tensor)
    score = lpips_tensor.item()
    
    return score


def eval_ssim(generated_image, truth_image):
    """
    Takes in two paths and returns the SSIM score.
    Inputs:
        generated_image: String; path to generated image
        truth_image: String; path to truth image
    Outputs:
        score: float; SSIM score
    """
    generated_image = Image.open(generated_image).convert('RGB')
    generated_array = np.array(generated_image)

    truth_image = Image.open(truth_image).convert("RGB")
    truth_array = np.array(truth_image)

    score = SSIM(generated_array, truth_array, multichannel=True)

    return score


def eval_psnr(generated_image, truth_image):
    """
    Takes in two paths and returns the PSNR score.
    Inputs:
        generated_image: String; path to generated image
        truth_image: String; path to truth image
    Outputs:
        score: float; PSNR score
    """
    generated_image = cv2.imread(generated_image)

    truth_image = cv2.imread(truth_image)

    score = cv2.PSNR(generated_image, truth_image)

    return score


def eval_fid(generated_folder, truth_folder, device="cpu"):
    """
    Takes in two paths (folders) and returns the FID score.
    Inputs:
        generated_folder: String; path to folder containing generated images
        truth_folder: String; path to folder containing truth images
        device: String: "cpu" or "cuda"
    Outputs:
        score: float; FID score
    """
    score = fid_score.calculate_fid_given_paths(
        [generated_folder, truth_folder],
        2,
        device,
        2048
    )

    return score

def eval_matrix_completion(generated_image, truth_image):
    """
    Takes in two paths and returns all scores except FID.
    Inputs:
        generated_image: String; path to generated image
        truth_image: String; path to truth image
    Outputs:
        scores: dictionary; PSNR score
    """
    scores = {
        "LPIPS": eval_lpips(generated_image, truth_image),
        "SSIM": eval_ssim(generated_image, truth_image),
        "PSNR": eval_psnr(generated_image, truth_image)
    }

    return scores