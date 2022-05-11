# CVPR 2022 Workshop on Multimodal Learning for Earth and Environment Submission and Evaluation Server
## About
This repository is the software used to recieve and evaluate submissions for the [CVPR 2022 Workshop on Multimodal Learning for Earth and Environment](https://sites.google.com/view/rainforest-challenge).

The paper for the challenge can be [found here](https://arxiv.org/abs/2204.07649).

## How It Works
We can provide this software under an open source license because the magic behind it is actually the truth data loaded onto it, which won't be released until after the conference, at the earliest.

The system itself is broken into a containerized frontend and backend. The frontend verifies that submission data is submitted in a format that can be compared to the truth data and displays overall metrics per team. The backend checks for new submissions every X amount of minutes, keeps metrics for every image, and updates the shared database with the overall metrics. 

## How To Use
### Full System
Using docker, the full system and be created with a simple `docker-compose up --build`. The `submission` and `db` volumes mounts can be left empty and populated by the system, but truth data needs to be mounted into the truth folder. Recommended file structure is as follows:
```
./truth
  |-- estimation
  |  |-- date01
  |  |  |-- deforestation_date01_lat_lon.png
  |  |  |-- ...
  |  |-- date02
  |  |  |-- deforestation_date02_lat_lon.png
  |  |  |-- ...
  |-- matrix-completion
  |  |-- dataset01
  |  |  |-- dataset01_lat_lon_mm_dd.tiff
  |  |  |-- ...
  |  |-- dataset02
  |  |  |-- dataset02_lat_lon_mm_dd.tiff
  |  |  |-- ...
  |-- translation
  |  |-- input_image_name01
  |  |  |-- truth_image01.png
  |  |  |-- ...
  |  |-- input_image_name01
  |  |  |-- truth_image01.png
  |  |  |-- ...
```

### Just Running Eval

---
**Note: This portion is untested. If you run into bugs, please submit an issue.**

---

It should be possible to run on-demand metrics with:
```Python
import translation.eval_submission as translation_eval
import estimation.eval_submission as estimation_eval
import matrix.eval_team as matrix_eval

translation_folder = './path/to/submission'
translation_scores = translation_eval(translation_folder, truth="/path/to/truth/folder")
print(translation_scores)

estimation_folder = './path/to/estimation'
estimation_scores = estimation_eval(estimation_folder, truth_folder="/path/to/truth/folder")

# needs to be refactored to be in line with other two
# actual submission would be located in ./parent/of/matrix/submssion
matrix_folder = './parent/of/matrix'
matrix_scores = matrix_eval(matrix_folder, "team")
```

## To Do
 - [ ] Standardize evaluation scripts
 - [ ] Add Homepage