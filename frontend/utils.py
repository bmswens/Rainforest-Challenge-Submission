# built in
from zipfile import ZipFile
import datetime
import os
import json

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


def verify(path, challenge):
    output = {
        "ok": True,
        "errors": []
    }
    with ZipFile(path) as archive:
        files = archive.namelist()
    # add one to account for parent folder
    if len(files) != config[challenge]["image_count"]:
        output["ok"] = False
        output["errors"].append(f"Expected {config[challenge]['image_count']} files, recieved {len(files)}")
    return output


def save(zip_path, challenge, team_name, emails):
    now = datetime.datetime.now()
    team_folder = f"submissions/valid/{challenge}/{team_name}/{now.isoformat().replace(':', '-')}"
    image_target = f"{team_folder}/images"
    os.makedirs(image_target, exist_ok=True)
    with ZipFile(zip_path) as archive:
        files = archive.namelist()
        to_extract = [f for f in files if config[challenge]["image_type"] in f]
        archive.extractall(image_target, to_extract)
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