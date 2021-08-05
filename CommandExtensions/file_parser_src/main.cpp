#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "blcmm.hpp"
#include "errors.hpp"
#include "parser.hpp"

namespace py = pybind11;

PYBIND11_MODULE(MODULE_NAME, m) {
    m.def("parse", &parse, py::arg("filename"), py::arg("cmd_names"));

    py::register_exception<parser_error>(m, "ParserError", PyExc_RuntimeError);

    py::enum_<enable_strategy>(m, "EnableStrategy")
        .value("All", enable_strategy::ALL)
        .value("Any", enable_strategy::ANY)
        .value("Force", enable_strategy::FORCE)
        .value("Next", enable_strategy::NEXT);

#ifdef MODULE_VERSION
    #define STRINGIFY(x) #x
    #define STRINGIFY_MACRO(x) STRINGIFY(x)
    m.attr("__version__") = STRINGIFY_MACRO(MODULE_VERSION);
#else
    m.attr("__version__") = "dev";
#endif
}
