import os
import shutil
from collections import OrderedDict
from configparser import ConfigParser
from fnmatch import fnmatch
from zipfile import ZIP_DEFLATED, ZipFile

"""
This is a quick helper script I use to add the zips into each folder - It is *not* meant to be run
 by the sdk, it's external.
"""

config = ConfigParser(defaults=OrderedDict(
    dont_zip="false",
    include_settings="false",
    ignore=""
))
config.read("zipper.ini")


for dir_entry in os.scandir():
    if not dir_entry.is_dir():
        continue

    if dir_entry.name[0] == ".":
        continue

    dont_zip = False
    ignores = ["settings.json"]
    if dir_entry.name in config:
        dont_zip = config[dir_entry.name].getboolean("dont_zip")

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

    for dir_path, _, file_names in os.walk(dir_entry.path):
        if os.path.basename(dir_path) == "__pycache__":
            shutil.rmtree(dir_path)
            continue
        for file in file_names:
            if file == zip_name:
                continue
            file_path = os.path.join(dir_path, file)

            for ig in ignores:
                if file == ig or fnmatch(file_path, ig):
                    os.remove(file_path)
                    break
            else:
                if not dont_zip:
                    zip_file.write(file_path)  # type: ignore

    if not dont_zip:
        zip_file.close()  # type: ignore
