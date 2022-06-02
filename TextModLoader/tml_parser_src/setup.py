import os
from distutils.core import setup
from glob import glob
from shutil import copyfile

from pybind11.setup_helpers import Pybind11Extension, build_ext

__version__ = "1.1"
MODULE_NAME = "tml_parser"

cwd = os.getcwd()
os.chdir(os.path.dirname(__file__))

setup(
    name=MODULE_NAME,
    version=__version__,
    ext_modules=[
        Pybind11Extension(
            MODULE_NAME,
            sorted(glob("**/*.cpp", recursive=True)),
            include_dirs=["lib"],
            define_macros=[
                ("MODULE_VERSION", __version__),
                ("MODULE_NAME", MODULE_NAME)
            ]
        )
    ],
    cmdclass={
        "build_ext": build_ext
    },
)

copyfile(glob("build/lib.*/" + MODULE_NAME + ".*.pyd")[0], "../" + MODULE_NAME + ".pyd")
os.chdir(cwd)
