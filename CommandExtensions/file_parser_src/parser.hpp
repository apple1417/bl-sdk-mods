#pragma once

#include <optional>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#if __has_include(<pybind11/pybind11.h>)
    #include <pybind11/pybind11.h>
    using encoded_str = pybind11::str;
    #define ENCODE(x) ((encoded_str)PyUnicode_Decode((x).data(), (x).length(), "cp1252", "strict"))
#else
    using encoded_str = std::string;
    #define ENCODE(x) ((encoded_str)x)
#endif

using split_command = std::optional<std::pair<std::string, std::string>>;

using command_list = std::vector<std::pair<encoded_str, encoded_str>>;
using command_names = std::unordered_set<std::string>;

split_command parse_possible_cmd(const std::string& cmd);

command_list parse(const std::string& filename, const command_names& cmd_names);
