#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "blcmm/blcmm.hpp"
#include "parse.hpp"

#ifdef _WIN32
#include <winerror.h>
#else
#include <errno.h>
#endif

#define STRINGIFY(x) #x
#define STRINGIFY_MACRO(x) STRINGIFY(x)

namespace py = pybind11;

/**
 * @brief Wrapper around `parse` to open a file and throw a file not found if needed.
 *
 * @param filename The file to look through.
 * @return A tuple of the extracted data.
 */
results_tuple parse_wrapper(std::string& file_path)
{
    if (!std::filesystem::exists(file_path)) {
#ifdef _WIN32
        PyErr_SetExcFromWindowsErrWithFilename(
            PyExc_FileNotFoundError,
            ERROR_FILE_NOT_FOUND,
            file_path.c_str()
        );
#else
        errno = ENOENT;
        PyErr_SetFromErrnoWithFilename(
            ERROR_FILE_NOT_FOUND,
            file_path.c_str()
        );
#endif
        throw py::error_already_set();
    }

    std::ifstream file{file_path};

    return parse(file);
}

/**
 * @brief Wrapper around `parse` to read from a string.
 *
 * @return A tuple of the extracted data.
 */
results_tuple parse_string(std::string& str)
{
    std::stringstream stream{str};
    return parse(stream);
}

PYBIND11_MODULE(MODULE_NAME, m) {
    m.attr("__version__") = STRINGIFY_MACRO(MODULE_VERSION);

    py::register_exception<blcmm_parser_error>(m, "BLCMMParserError", PyExc_RuntimeError);

    m.def("parse", &parse_wrapper, py::arg("file_path"));
    m.def("parse_string", &parse_string, py::arg("str"));
}
