#include "blcmm.hpp"

#include "errors.hpp"
#include "parser.hpp"

#include <pugixml-1.11/pugixml.hpp>

#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static void put_xml_escaped(char c, std::ostream& stream) {
    switch (c) {
        case '"': stream << "&quot;"; break;
        case '\'': stream << "&apos;"; break;
        case '<': stream << "&lt;"; break;
        case '>': stream << "&gt;"; break;
        case '&': stream << "&amp;"; break;
        default: stream << c; break;
    }
}

static void preprocess_file(std::istream& blcmm_input, std::ostream& xml_output) {
    for (std::string line; std::getline(blcmm_input, line); ) {
        // Stop after the end of the blcmm section
        if (line.rfind("</BLCMM>", 0) == 0) {
            xml_output << line;
            break;
        }
        // Ignore the filtertool warning
        if (line.rfind("#<!!!", 0) == 0) {
            continue;
        }

        auto tag_start = line.find_first_of('<');
        if (tag_start == std::string::npos) {
            throw parser_error("Failed to parse line (couldn't find inital tag): " + line);
        }

        auto tag_name_end = line.find_first_of("> ", tag_start);
        if (tag_name_end == std::string::npos) {
            throw parser_error("Failed to parse line (inital tag doesn't close): " + line);
        }
        xml_output << line.substr(tag_start, tag_name_end - tag_start + 1);

        auto content_start = tag_name_end + 1;

        if (line[tag_name_end] != '>') {
            auto tag_body_section_start = content_start;
            while (true) {
                auto tag_body_section_end = line.find_first_of("\">", tag_body_section_start);
                if (tag_body_section_end == std::string::npos) {
                    throw parser_error("Failed to parse line (inital tag doesn't close): " + line);
                }
                xml_output << line.substr(
                    tag_body_section_start,
                    tag_body_section_end - tag_body_section_start + 1
                );
                if (line[tag_body_section_end] == '>') {
                    break;
                }

                auto attr_val_end = tag_body_section_end;
                do {
                    attr_val_end = line.find_first_of('"', attr_val_end + 1);
                    if (attr_val_end == std::string::npos) {
                        throw parser_error(
                            "Failed to parse line (attribute value doesn't close): " + line
                        );
                    }
                } while (line[attr_val_end - 1] == '\\');

                for (size_t i = tag_body_section_end + 1; i < attr_val_end; i++) {
                    put_xml_escaped(line[i], xml_output);
                }
                xml_output << '"';

                tag_body_section_start = attr_val_end + 1;
            }

            content_start = tag_body_section_start + 1;
        }

        auto closing_tag_str = (
            "</" + line.substr(tag_start + 1, tag_name_end - tag_start - 1) + ">"
        );
        auto closing_tag_start = line.rfind(closing_tag_str);
        if (closing_tag_start != std::string::npos) {
            for (size_t i = content_start; i < closing_tag_start; i++) {
                put_xml_escaped(line[i], xml_output);
            }

            xml_output << closing_tag_str;
        }
    }

    if (blcmm_input.fail()) {
        if (blcmm_input.eof()) {
            throw io_error("Error while reading input (eof)");
        }
        throw io_error("Error while reading input");
    }

    if (xml_output.fail()) {
        throw io_error("Error while writing output");
    }
}

static bool in_comma_seperated_list(const std::string& value, const std::string& list) {
    size_t entry_start = 0;
    while (entry_start < list.size()) {
        auto entry_end = list.find_first_of(',', entry_start);
        if (list.compare(entry_start, entry_end - entry_start, value) == 0) {
            return true;
        };
        if (entry_end == std::string::npos) {
            break;
        }
        entry_start = entry_end + 1;
    }
    return false;
}

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
                    ENCODE((*split).first),
                    ENCODE((*split).second)
                });
            } else {
                cached_commands.push_back({
                    ENCODE((*split).first),
                    ENCODE((*split).second)
                });
            }

        } else if (child_name == "code") {
            auto is_enabled = in_comma_seperated_list(
                profile,
                child.attribute("profiles").as_string()
            );
            switch (strategy) {
            case enable_strategy::ALL: {
                if (!is_enabled) {
                    strategy_group_state = true;
                }
                break;
            }
            case enable_strategy::ANY: {
                if (is_enabled) {
                    strategy_group_state = true;
                }
                break;
            }
            case enable_strategy::FORCE: break;
            case enable_strategy::NEXT: {
                if (is_enabled) {
                    output.insert(output.end(), cached_commands.begin(), cached_commands.end());
                }
                cached_commands.clear();
                break;
            }
            }
        }
    }

    on_block_end();
}

command_list handle_blcmm_file(std::istream& file, const command_names& cmd_names) {
    std::stringstream processed_xml{};
    preprocess_file(file, processed_xml);

    pugi::xml_document doc{};
    auto res = doc.load(processed_xml, pugi::parse_default, pugi::encoding_latin1);
    if (res.status != pugi::status_ok) {
        if (res.status == pugi::status_io_error) {
            throw io_error(res.description());
        }
        throw parser_error(res.description());
    }

    auto profile = doc.select_node(
        "/BLCMM/head/profiles/profile[@name][@current='true']/@name"
    ).attribute().as_string("default");

    auto root = doc.select_node("/BLCMM/body/category").node();
    if (root == nullptr) {
        throw parser_error("Couldn't find root category");
    }

    command_list output{};
    handle_category(root, enable_strategy::ANY, output, profile, cmd_names);

    return output;
}
