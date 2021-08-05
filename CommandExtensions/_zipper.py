import os
import shutil
from distutils.core import run_setup
from zipfile import ZIP_DEFLATED, ZipFile

MODULE_NAME = "file_parser.pyd"
MODULE_DIR_NAME = "file_parser_src"

folder_path = os.path.abspath(os.path.dirname(__file__))
folder_name = os.path.basename(folder_path)

module_setup_path = os.path.join(folder_path, MODULE_DIR_NAME, "setup.py")
run_setup(module_setup_path, ["build"])

zip_path = os.path.join(folder_path, folder_name + ".zip")
ignored_files = (
    zip_path,
    os.path.abspath(__file__)
)

with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=9) as zip_file:
    for dir_path, dir_names, file_names in os.walk(folder_path):
        current_dir = os.path.basename(dir_path)
        if current_dir == "__pycache__":
            shutil.rmtree(dir_path)
            continue
        elif current_dir == MODULE_DIR_NAME:
            dir_names[:] = []
            continue

        for file in file_names:
            file_path = os.path.join(dir_path, file)
            if file_path in ignored_files:
                continue

            rel_path = os.path.relpath(file_path, os.path.join(folder_path, ".."))
            zip_file.write(file_path, rel_path)

    license_path = os.path.join(folder_path, "..", "LICENSE")
    license_zip_path = os.path.join(folder_name, "LICENSE")
    zip_file.write(license_path, license_zip_path)

os.system(f"git add {os.path.join(folder_path, MODULE_NAME)}")
