# built in
from zipfile import ZipFile
import datetime
import os
import json

#3rd Party
from PIL import Image
from flask import current_app

# custom
from config import config

def get_files(path, f_type):
    output = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f_type in f:
                relative_path = os.path.join(root, f).replace(path, '')
                output.append(relative_path)
    return output


def verify_c3(path, verify_path="/app/c3_files.json"):
    output = {
        "ok": True,
        "errors": []
    }
    with ZipFile(path) as archive:
        files = archive.namelist()
    with open('/app/truth/translation/files.json') as incoming:
        items = json.load(incoming)
    for key in items:
        for f in eval(key):
            f_path = os.path.join('translation', f)
            if f_path not in files:
                output["ok"] = False
                output["errors"].append(f"Missing file: {f_path}")
                return output
    return output


def verify(path, challenge, f_type):
    output = {
        "ok": True,
        "errors": []
    }
    if challenge == "translation": 
        return output
    with ZipFile(path) as archive:
        files = [f for f in archive.namelist()]
        expected_files = get_files(f'/app/truth/{challenge}', f_type)
        if challenge in ['fire', 'estimation']:
            files = [f.lower() for f in files]
            expected_files = [f.lower() for f in expected_files]
        for f in expected_files:
            f = f[1:]
            if f not in files:
                output["errors"].append(f'Missing file: {f}')
                output["ok"] = False
            if challenge == "matrix-completion":
                img = Image.open(archive.open(f))
                if img.height != 256 or img.width != 256:
                    output["errors"].append(f'File {f} should be 256x256 but was {img.height}x{img.width}')
                    output["ok"] = False
    return output


def lowercase_all_files(dir):
    starting_dir = os.getcwd()
    os.chdir(dir)
    for f in os.listdir('.'):
        os.rename(f, f.lower())
    os.chdir(starting_dir)


def save(zip_path, challenge, team_name, emails):
    now = datetime.datetime.now()
    team_folder = f"submissions/valid/{challenge}/{team_name}/{now.isoformat().replace(':', '-')}"
    image_target = f"{team_folder}/images"
    os.makedirs(image_target, exist_ok=True)
    with ZipFile(zip_path) as archive:
        files = archive.namelist()
        to_extract = [f for f in files if config[challenge]["image_type"] in f]
        archive.extractall(image_target, to_extract)
    # all lowercase
    if challenge in ['fire', 'estimation']:
        lowercase_all_files(os.path.join(image_target, challenge))
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
