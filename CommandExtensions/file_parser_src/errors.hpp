#pragma once

#include <stdexcept>
#include <string>

#if __has_include(<pybind11/pybind11.h>)
    #include <pybind11/pybind11.h>
    using error_type = pybind11::error_already_set;
#else
    using error_type = std::runtime_error;
#endif

class parser_error : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

error_type file_not_found(std::string filename);
error_type io_error(std::string msg);
