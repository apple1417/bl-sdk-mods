#include "parse.hpp"

#include <algorithm>
#include <istream>
#include <optional>
#include <sstream>
#include <string>
#include <utility>

#include <pugixml-1.11/pugixml.hpp>

#include "blcmm/blcmm.hpp"

using split_command = std::optional<std::pair<std::string, std::string>>;

/**
 * @brief Given a string, try parse a command out of it.
 *
 * @param cmd The string to look through.
 * @return A pair of (lowercase) command to it's args, or std::nullopt if no command was found.
 */
static split_command parse_possible_cmd(const std::string& cmd) {
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

/**
 * @brief Recusively look through BLCMM categories and extract all enabled commands within them.
 *
 * @param category The XML category to look through.
 * @param strategy The current enable strategy.
 * @param output The list of commands to output to.
 * @param profile The file's selected profile.
 * @param cmd_names The set of valid command names.
 */
static void handle_category(
    const pugi::xml_node category,
    enable_strategy strategy,
    command_list& output,
    const std::string& profile,
    const command_names& cmd_names
) {
    /*
    All - stores all commands until the end of the block
    Any - stores all commands until the end of the block
    Force - ignored
    Next - stores all commands until the next enabled category
    */
    command_list cached_commands{};

    /*
    All - true if we've seen any disabled categories
    Any - true if we've seen any enabled categories
    Ignored for others
    */
    bool strategy_group_state = false;

    auto on_block_end = [&]{
        if (
            // Didn't see any disabled categorys
            (strategy == enable_strategy::ALL && !strategy_group_state)
            // Saw an enabled category
            || (strategy == enable_strategy::ANY && strategy_group_state)
            // Force and Next don't do anything on block end
        ) {
            output.insert(output.end(), cached_commands.begin(), cached_commands.end());
        }

        cached_commands.clear();
        strategy_group_state = false;
    };

    auto update_enable_strategy = [&](const std::string& val){
        auto word_idx = val.find_first_not_of(' ');
        if (word_idx == std::string::npos) {
            return false;
        }
        auto space_idx = val.find_first_of(' ', word_idx + 1);
        auto strategy_name = val.substr(word_idx, space_idx - word_idx);
        std::transform(
            strategy_name.begin(),
            strategy_name.end(),
            strategy_name.begin(),
            [](unsigned char c){ return std::tolower(c); }
        );

        on_block_end();

        if (strategy_name == "all") {
            strategy = enable_strategy::ALL;
        } else if (strategy_name == "any") {
            strategy = enable_strategy::ANY;
        } else if (strategy_name == "force") {
            strategy = enable_strategy::FORCE;
        } else if (strategy_name == "next") {
            strategy = enable_strategy::NEXT;
        } else {
            return false;
        }
        return true;
    };

    // Quick pass to pull hotfixes out a level
    std::vector<pugi::xml_node> all_child_nodes;
    for (auto child : category) {
        std::string child_name = child.name();
        if (child_name == "hotfix") {
            all_child_nodes.insert(all_child_nodes.end(), child.begin(), child.end());
        } else {
            all_child_nodes.push_back(child);
        }
    }

    // Main pass through
    for (auto child : all_child_nodes) {
        std::string child_name = child.name();
        if (child_name == "category") {
            handle_category(child, strategy, output, profile, cmd_names);
            continue;

        } else if (child_name == "comment") {
            auto split = parse_possible_cmd(child.child_value());
            if (!split) {
                continue;
            }
            if ((*split).first == "ce_enableon") {
                if (update_enable_strategy((*split).second)) {
                    continue;
                }
            }
            if (!cmd_names.contains((*split).first)) {
                continue;
            }

            if (strategy == enable_strategy::FORCE) {
                output.push_back({
                    (*split).first,
                    (*split).second
                });
            } else {
                cached_commands.push_back({
                    (*split).first,
                    (*split).second
                });
            }

        } else if (child_name == "code") {
            auto is_enabled = in_comma_seperated_list(
                profile,
                child.attribute("profiles").as_string()
            );
            switch (strategy) {
                case enable_strategy::ALL:
                    if (!is_enabled) {
                        strategy_group_state = true;
                    }
                    break;
                case enable_strategy::ANY:
                    if (is_enabled) {
                        strategy_group_state = true;
                    }
                    break;
                case enable_strategy::FORCE:
                    break;
                case enable_strategy::NEXT:
                    if (is_enabled) {
                        output.insert(output.end(), cached_commands.begin(), cached_commands.end());
                    }
                    cached_commands.clear();
                    break;
            }
        }
    }

    on_block_end();
}

/**
 * @brief Extract all enabled custom commands stored in a BLCMM file.
 *
 * @param stream A stream containing the BLCMM file to parse.
 * @param cmd_names The set of valid command names.
 * @return A list of all enabled custom commands.
 */
static command_list handle_blcmm_file(std::istream& stream, const command_names& cmd_names) {
    std::stringstream processed_xml{};
    preprocess_blcmm_file(stream, processed_xml);

    pugi::xml_document doc{};
    auto res = doc.load(processed_xml, pugi::parse_default, pugi::encoding_latin1);
    if (res.status != pugi::status_ok) {
        throw blcmm_parser_error(res.description());
    }

    auto profile = doc.select_node(
        "/BLCMM/head/profiles/profile[@name][@current='true']/@name"
    ).attribute().as_string("default");

    auto root = doc.select_node("/BLCMM/body/category").node();
    if (root == nullptr) {
        throw blcmm_parser_error("Couldn't find root category");
    }

    command_list output{};
    handle_category(root, enable_strategy::ANY, output, profile, cmd_names);

    return output;
}

command_list parse(std::istream& stream, const command_names& cmd_names) {
    std::string line;
    std::getline(stream, line);
    stream.seekg(0);

    if (line.rfind("<BLCMM", 0) == 0) {
        return handle_blcmm_file(stream, cmd_names);
    }

    // Fall back to line by line implementation
    command_list output{};
    while (std::getline(stream, line)) {
        auto split = parse_possible_cmd(line);
        if (split && cmd_names.contains((*split).first)) {
            output.push_back({
                (*split).first,
                (*split).second
            });
        }
    }

    return output;
}
