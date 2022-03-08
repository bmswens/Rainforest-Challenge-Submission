# built in
from zipfile import ZipFile

# custom
import config


def contents(path):
    output = {
        "ok": True,
        "errors": []
    }
    with ZipFile(path) as archive:
        files = archive.namelist()
    # add one to account for parent folder
    if len(files) != config.n_images:
        output["ok"] = False
        output["errors"].append(f"Expected {config.n_images} files, recieved {len(files)}")
    return output