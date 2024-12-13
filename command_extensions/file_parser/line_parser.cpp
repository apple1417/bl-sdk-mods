#include "pch.h"
#include "matcher.h"

namespace ce {

std::vector<CommandMatch> parse_file_line_by_line(std::istream& stream) {
    std::vector<CommandMatch> output{};

    std::string line;
    while (std::getline(stream, line)) {
        auto [cmd, match] = try_match_command(line);
        if (cmd.empty()) {
            continue;
        }

        static const constexpr CaseInsensitiveStringView new_cmd = "CE_NewCmd";
        if (cmd == new_cmd) {
            add_new_command(std::string_view{line}.substr(match.cmd_len));
            continue;
        }

        output.emplace_back(std::move(match));
    }

    return output;
}

}  // namespace ce
