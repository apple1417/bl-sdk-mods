#include "parser.hpp"

#include "blcmm.hpp"
#include "errors.hpp"

#include <filesystem>
#include <fstream>
#include <string>
#include <utility>

split_command parse_possible_cmd(const std::string& cmd) {
    auto word_idx = cmd.find_first_not_of(' ');
    if (word_idx == std::string::npos) {
        return std::nullopt;
    }
    auto space_idx = cmd.find_first_of(' ', word_idx + 1);
    if (space_idx == std::string::npos) {
        return std::nullopt;
    }

    auto cmd_name = cmd.substr(word_idx, space_idx - word_idx);
    std::transform(
        cmd_name.begin(),
        cmd_name.end(),
        cmd_name.begin(),
        [](unsigned char c){ return std::tolower(c); }
    );
    std::pair<std::string, std::string> ret = { cmd_name, cmd.substr(space_idx + 1) };
    return { ret };
}

command_list parse(const std::string& filename, const command_names& cmd_names) {
    if (!std::filesystem::exists(filename)) {
        throw file_not_found(filename);
    }

    std::ifstream file{filename};
    std::string line;
    std::getline(file, line);
    file.seekg(0);

    if (line.rfind("<BLCMM", 0) == 0) {
        return handle_blcmm_file(file, cmd_names);
    }

    command_list output{};
    while (std::getline(file, line)) {
        auto split = parse_possible_cmd(line);
        if (split && cmd_names.contains((*split).first)) {
            output.push_back({
                ENCODE((*split).first),
                ENCODE((*split).second)
            });
        }
    }

    return output;
}
