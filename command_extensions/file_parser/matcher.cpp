#include "pch.h"
#include "matcher.h"

namespace ce {

#pragma region Case insensitive String

bool CaseInsensitiveTraits::eq(char chr_a, char chr_b) {
    return std::tolower(chr_a) == std::tolower(chr_b);
}
bool CaseInsensitiveTraits::lt(char chr_a, char chr_b) {
    return std::tolower(chr_a) < std::tolower(chr_b);
}
int CaseInsensitiveTraits::compare(const char* chr_a, const char* chr_b, size_t n) {
    while (n-- != 0) {
        if (std::tolower(*chr_a) < std::tolower(*chr_b)) {
            return -1;
        }
        if (std::tolower(*chr_a) > std::tolower(*chr_b)) {
            return 1;
        }
        ++chr_a;
        ++chr_b;
    }
    return 0;
}

CaseInsensitiveStringView::CaseInsensitiveStringView(std::string_view str)
    : CaseInsensitiveStringView(str.data(), str.size()) {}

bool CaseInsensitiveStringView::operator==(std::string_view str) const {
    return *this == CaseInsensitiveStringView{str.data(), str.size()};
}

#pragma endregion

#pragma region Command List

namespace {

// To match strings somewhat efficently we'll use a binary search - while not profiled I don't think
// we have enough strings and enough matching prefixes to make a full radix trie worth it.

// For this we need to keep our list of commands sorted.
std::vector<CaseInsensitiveString> sorted_commands;

}  // namespace

void update_commands(std::vector<CaseInsensitiveString>& commands) {
    sorted_commands = std::move(commands);
    std::sort(sorted_commands.begin(), sorted_commands.end());
}

void add_new_command(CaseInsensitiveStringView cmd) {
    auto non_space =
        std::find_if_not(cmd.begin(), cmd.end(), [](auto chr) { return std::isspace(chr); });
    if (non_space == cmd.end()) {
        return;
    }
    auto cmd_name_end =
        std::find_if(non_space, cmd.end(), [](auto chr) { return std::isspace(chr); });
    if (cmd_name_end != cmd.end()) {
        // Make sure there are no extra spaces
        auto next_space =
            std::find_if(cmd_name_end, cmd.end(), [](auto chr) { return std::isspace(chr); });
        if (next_space != cmd.end()) {
            // Give up
            return;
        }
    }

    CaseInsensitiveString cmd_name{non_space, cmd_name_end};
    sorted_commands.insert(
        std::lower_bound(sorted_commands.begin(), sorted_commands.end(), cmd_name), cmd_name);
}

#pragma endregion

#pragma region Command Matching

CommandMatch::CommandMatch(std::string_view line) : cmd_len(0) {
    auto non_space =
        std::find_if_not(line.begin(), line.end(), [](auto chr) { return std::isspace(chr); });
    if (non_space == line.end()) {
        return;
    }

    auto cmd_end = std::find_if(non_space, line.end(), [](auto chr) { return std::isspace(chr); });
    if (cmd_end == line.end()) {
        return;
    }

    CaseInsensitiveStringView cmd{non_space, cmd_end};
    if (!std::binary_search(sorted_commands.begin(), sorted_commands.end(), cmd)) {
        return;
    }

    this->cmd = {non_space, cmd_end};
    this->py_cmd = py::reinterpret_steal<py::object>(
        PyUnicode_DecodeLocaleAndSize(cmd.data(), (Py_ssize_t)cmd.size(), nullptr));
    this->line = py::reinterpret_steal<py::object>(
        PyUnicode_DecodeLocaleAndSize(line.data(), (Py_ssize_t)line.size(), nullptr));
    this->cmd_len = cmd_end - line.begin();
}

CommandMatch::operator bool() const {
    return (bool)this->py_cmd;
}

#pragma endregion

}  // namespace ce
