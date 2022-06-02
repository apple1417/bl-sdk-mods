#include <filesystem>
#include <fstream>
#include <string>
#include <utility>
#include <vector>

#include <windows.h>
#include <winerror.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "blcmm/blcmm.hpp"

#include "parse.hpp"

#define STRINGIFY(x) #x
#define STRINGIFY_MACRO(x) STRINGIFY(x)

namespace py = pybind11;
using encoded_command_list = std::vector<std::pair<py::str, py::str>>;

/**
 * @brief Encodes a string to a python string using the default system code page.
 *
 * @param str The string to encode.
 * @return An encoded python string.
 */
static py::str encode_system(const std::string& str) {
    const auto encoding = "cp" + std::to_string(GetACP());

    return (py::str)PyUnicode_Decode(str.c_str(), str.length(), encoding.c_str(), "replace");
}

/**
 * @brief Wrapper around `parse`, adding some python specific functionaliy.
 * @note Opens a file and throws a file not found if needed
 * @note Encodes all output strings using the default system code page.
 *
 * @param filename The file to look through.
 * @param cmd_names A set of valid command names, all in lowercase.
 * @return A tuple of the extracted data.
 */
static encoded_command_list parse_wrapper(const std::string& filename, const command_names& cmd_names)
{
    if (!std::filesystem::exists(filename)) {
        PyErr_SetExcFromWindowsErrWithFilename(
            PyExc_FileNotFoundError,
            ERROR_FILE_NOT_FOUND,
            filename.c_str()
        );
        throw py::error_already_set();
    }


    encoded_command_list encoded_output;

    std::ifstream file{filename};
    for (auto command : parse(file, cmd_names)) {
        /*
        Technically it's wrong to just encode everything like this, it only applies to BLCMM
         files, theoretically someone could have a normal text file that's actually utf16.
        Practically, we'll hardly ever encounter normal text files, and ontop of that we'll
         hardly ever encounter non-ascii, so it's simpler just to encode everything.
        */
        encoded_output.push_back({encode_system(command.first), encode_system(command.second)});
    }

    return encoded_output;
}

PYBIND11_MODULE(MODULE_NAME, m) {
    m.attr("__version__") = STRINGIFY_MACRO(MODULE_VERSION);
    py::register_exception<blcmm_parser_error>(m, "BLCMMParserError", PyExc_RuntimeError);

    m.def("parse", &parse_wrapper, py::arg("filename"), py::arg("cmd_names"));

    py::enum_<enable_strategy>(m, "EnableStrategy")
        .value("All", enable_strategy::ALL)
        .value("Any", enable_strategy::ANY)
        .value("Force", enable_strategy::FORCE)
        .value("Next", enable_strategy::NEXT);
}
