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


def verify(path, challenge, f_type):
    output = {
        "ok": True,
        "errors": []
    }
    if challenge == "translation": 
        return output
    with ZipFile(path) as archive:
        files = archive.namelist()
    expected_files = get_files(f'/app/truth/{challenge}', f_type)
    for f in expected_files:
        f = f[1:]
        if f not in files:
            output["errors"].append(f'Missing file: {f}')
            output["ok"] = False
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