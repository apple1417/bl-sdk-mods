#include "errors.hpp"

#if __has_include(<pybind11/pybind11.h>)

#include <pybind11/pybind11.h>
#ifdef _WIN32
#include <winerror.h>
#else
#include <errno.h>
#endif

namespace py = pybind11;

error_type file_not_found(std::string filename) {
#ifdef _WIN32
    PyErr_SetExcFromWindowsErrWithFilename(
        PyExc_FileNotFoundError,
        ERROR_FILE_NOT_FOUND,
#else
    errno = ENOENT;
    PyErr_SetFromErrnoWithFilename(
        ERROR_FILE_NOT_FOUND,
#endif
        filename.c_str()
    );
    return py::error_already_set();
}

error_type io_error(std::string msg) {
    PyErr_SetString(
        PyExc_IOError,
        msg.c_str()
    );
    return py::error_already_set();
}

#else

error_type file_not_found(std::string filename) {
    return std::runtime_error("File not found: " + filename);
}

error_type io_error(std::string msg) {
    return std::runtime_error(msg);
}

#endif
