import os
import shutil
import subprocess
from argparse import ArgumentParser
from collections import OrderedDict
from configparser import ConfigParser
from fnmatch import fnmatch
from zipfile import ZIP_DEFLATED, ZipFile

"""
This is a quick helper script I use to add the zips into each folder - It is *not* meant to be run
 by the sdk, it's external.
"""

parser = ArgumentParser(description="Cleanup and zip all mod folders.")
parser.add_argument(
    "--git-staged",
    action="store_true",
    help="Only zip folders that contain files currently staged in git."
)
parser.add_argument(
    "--dont-zip",
    action="store_true",
    help="Don't create any zip files, just clean out the folders."
)
args = parser.parse_args()

config = ConfigParser(defaults=OrderedDict(
    dont_zip="false",
    include_settings="false",
    ignore=""
))
config.read("zipper.ini")

git_whitelist = set()
if args.git_staged:
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--staged"],
        stdout=subprocess.PIPE,
        encoding="utf8"
    )

    for file in proc.stdout.splitlines():
        curr_path = os.path.normpath(file)
        new_path = os.path.dirname(curr_path)
        if new_path == "":
            continue
        while new_path != "":
            curr_path = new_path
            new_path = os.path.dirname(curr_path)
        git_whitelist.add(curr_path)


for dir_entry in os.scandir():
    if not dir_entry.is_dir():
        continue

    if dir_entry.name[0] == ".":
        continue
    if args.git_staged and dir_entry.name not in git_whitelist:
        continue

    dont_zip = args.dont_zip
    ignores = ["settings.json"]
    if dir_entry.name in config:
        dont_zip = dont_zip or config[dir_entry.name].getboolean("dont_zip")

        if config[dir_entry.name].getboolean("include_settings"):
            ignores.remove("settings.json")
        ignores += [x for x in config[dir_entry.name]["ignore"].split(",") if len(x) > 0]

    zip_name = dir_entry.name + ".zip"
    zip_path = os.path.join(dir_entry.path, zip_name)
    zip_file = None
    if not dont_zip:
        try:
            os.remove(zip_path)
        except FileNotFoundError:
            pass

        zip_file = ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=9)

        license_path = os.path.join(os.path.basename(dir_entry.path), "LICENSE")
        zip_file.write("LICENSE", license_path)

    for dir_path, _, file_names in os.walk(dir_entry.path):
        if os.path.basename(dir_path) == "__pycache__":
            shutil.rmtree(dir_path)
            continue
        for file in file_names:
            if file == zip_name:
                continue
            file_path = os.path.join(dir_path, file)
            rel_path = os.path.relpath(file_path, dir_entry.path)

            for ig in ignores:
                if file == ig or fnmatch(rel_path, ig):
                    os.remove(file_path)
                    break
            else:
                if not dont_zip:
                    zip_file.write(file_path)  # type: ignore

    if not dont_zip:
        zip_file.close()  # type: ignore
