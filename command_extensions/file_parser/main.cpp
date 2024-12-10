#include "pch.h"

PYBIND11_MODULE(file_parser, mod) {
    mod.attr("__version__") = "3";
}
