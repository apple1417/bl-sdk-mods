#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
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
using encoded_comments_list = std::vector<py::str>;
using encoded_game = std::optional<py::str>;
using encoded_results_tuple = std::tuple<spark_service, game, encoded_comments_list>;

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
 * @param file_path The file to look through.
 * @return A tuple of the extracted data.
 */
encoded_results_tuple parse_wrapper(const std::string& file_path) {
    if (!std::filesystem::exists(file_path)) {
        PyErr_SetExcFromWindowsErrWithFilename(
            PyExc_FileNotFoundError,
            ERROR_FILE_NOT_FOUND,
            file_path.c_str()
        );
        throw py::error_already_set();
    }

    std::ifstream file{file_path};
    auto output = parse(file);

    encoded_comments_list comments;
    for (auto comment : std::get<2>(output)) {
        comments.push_back(encode_system(comment));
    }

    auto game = std::get<1>(output);
    return {
        std::get<0>(output),
        game.has_value() ? encoded_game{encode_system(game.value())} : std::nullopt,
        comments
    };
}

/**
 * @brief Wrapper around `parse` to read from a string.
 * @note No need to deal with encoding as pybind will make sure it's utf-8 on both ends.
 *
 * @return A tuple of the extracted data.
 */
results_tuple parse_string(const std::string& str) {
    std::stringstream stream{str};
    return parse(stream);
}

PYBIND11_MODULE(MODULE_NAME, m) {
    m.attr("__version__") = STRINGIFY_MACRO(MODULE_VERSION);

    py::register_exception<blcmm_parser_error>(m, "BLCMMParserError", PyExc_RuntimeError);

    m.def("parse", &parse_wrapper, py::arg("file_path"));
    m.def("parse_string", &parse_string, py::arg("str"));
}
