#include "parse.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>
#include <vector>

#include <pugixml-1.11/pugixml.hpp>

#include "blcmm/blcmm.hpp"

/**
 * @brief Trims leading whitespace in a string.
 *
 * @param str The string to trim.
 * @return A new trimmed string.
 */
static std::string trim_leading_whitespace(std::string str) {
    auto c = str.begin();
    for (; c != str.end(); c++) {
       if (!std::isspace(*c)) {
           break;
       }
    }
    return str.substr(c - str.begin());
}

/**
 * @brief Trims whitespace on both sides of a string.
 *
 * @param str The string to trim.
 * @return A new trimmed string.
 */
static std::string trim_whitespace(std::string str) {
    auto start = str.begin();
    auto end = str.begin();
    auto first_char = false;
    for (auto c = str.begin(); c != str.end(); c++) {
       if (!std::isspace(*c)) {
           if (!first_char) {
               start = c;
               first_char = true;
           } else {
               end = c;
           }
       }
    }
    return str.substr(start - str.begin(), end - start + 1);
}

/**
 * @brief Checks if the given line starts with a command.
 * @note Does not trim leading whitespace, must be done seperately.
 *
 * @param line The line to compare.
 * @param no_set Set to true to disable checking for `set` commands.
 * @return True if the line contains a command, false otherwise.
 */
static bool is_command(std::string line, bool no_set = false) {
    return line.rfind("exec", 0) == 0
           || line.rfind("say", 0) == 0
           || (!no_set && line.rfind("set", 0) == 0);
}

/**
 * @brief Returns true if the given category should be considered the description.
 *
 * @param category_name The category name.
 * @return True if this is a description category, false otherwise.
 */
static bool is_description_category(std::string category_name) {
    const std::string DESCRIPTION = "description";
    auto it = std::search(
        category_name.begin(), category_name.end(),
        DESCRIPTION.begin(), DESCRIPTION.end(),
        [](char a, char b) { return std::tolower(a) == std::tolower(b); }
    );
    return it != category_name.end();
}

/**
 * @brief Extract comments from a generic mod file.
 * @note Leaves the input stream on the first command.
 *
 * @param input The input stream to look though.
 * @return A list of extracted comments.
 */
static comments_list extract_generic_comments(std::istream& input) {
    comments_list comments;

    for (std::string line; std::getline(input, line); ) {
        if (is_command(trim_leading_whitespace(line))) {
            input.seekg(-(ptrdiff_t)line.size(), std::ios::cur);
            return comments;
        }
        comments.push_back(line);
    }

    // It might not actually be a mod file at all - want to be able to detect that.
    throw std::runtime_error("Didn't find any commands in generic mod file!");
}

/**
 * @brief Extract comments from a filtertool file.
 * @note Leaves the input stream directly after the point where comments finish, on the first
 *       command or category header.
 *
 * @param input The input stream to look though.
 * @return A list of extracted comments.
 */
static comments_list extract_filtertool_comments(std::istream& input) {
    comments_list comments;
    auto found_description = false;

    // Discard the first line (root category header)
    std::string line;
    std::getline(input, line);

    for (; std::getline(input, line); ) {
        auto trimmed = trim_whitespace(line);
        if (trimmed.rfind("#<", 0) == 0 && trimmed[trimmed.size() - 1] == '>') {
            if (!found_description) {
                auto category_name = trimmed.substr(2, trimmed.size() - 3);
                if (is_description_category(category_name)) {
                    found_description = true;
                    comments.clear();
                    continue;
                }
            }

            input.seekg(-(ptrdiff_t)line.size(), std::ios::cur);
            break;
        } else if (is_command(trimmed)) {
            input.seekg(-(ptrdiff_t)line.size(), std::ios::cur);
            break;
        } else {
            comments.push_back(line);
        }
    }

    return comments;
}

/**
 * @brief Extract comments from a blcmm file.
 *
 * @param doc A parsed pugixml document to look through.
 * @return A list of extracted comments.
 */
static comments_list extract_blcmm_comments(pugi::xml_document& doc) {
    std::string version = doc.select_node("/BLCMM/@v").attribute().as_string();
    if (version != "1") {
        throw blcmm_parser_error("Unknown BLCMM file version");
    }

    auto root = doc.select_node("/BLCMM/body/category").node();
    if (root == nullptr) {
        throw blcmm_parser_error("Couldn't find root category");
    }

    comments_list comments;

    for (auto child : root) {
        std::string child_name = child.name();
        if (child_name == "category") {
            auto category_name = child.attribute("name").as_string();
            if (is_description_category(category_name)) {
                comments.clear();

                for (auto grandchild : child) {
                    std::string grandchild_name = grandchild.name();
                    if (grandchild_name == "comment") {
                        auto comment = grandchild.child_value();
                        if (is_command(comment, true)) {
                            break;
                        }
                        comments.push_back(comment);
                    } else {
                        break;
                    }
                }
            }
            break;
        } else if (child_name == "comment") {
            auto comment = child.child_value();
            if (is_command(comment, true)) {
                break;
            }
            comments.push_back(comment);
        } else {
            break;
        }
    }

    return comments;
}

/**
 * @brief Looks through an input stream for commands matching hotfix ones, and extracts the service.
 *
 * @param input The input stream to look though.
 * @return The found service index, or `std::nullopt` if unsuccessful.
 */
static spark_service look_for_spark_service(std::istream& input) {
    for (std::string line; std::getline(input, line); ) {
        const std::string set = "set";
        const std::string transient = "Transient.SparkServiceConfiguration_";
        const std::string keys = "Keys";
        const std::string values = "Values";

        auto set_offset = line.find(set);
        if (set_offset == std::string::npos) {
            continue;
        }

        auto transient_offset = line.find(transient, set_offset + set.size() + 1);
        if (transient_offset == std::string::npos) {
            continue;
        }

        auto transient_end = transient_offset + transient.size();
        size_t count;
        auto idx = std::stoi(line.substr(transient_offset + transient.size()), &count);

        auto keys_offset = line.find(keys, transient_end + count + 1);
        auto values_offset = line.find(values, transient_end + count + 1);
        if (keys_offset == std::string::npos && values_offset == std::string::npos) {
            continue;
        }

        return idx;
    }

    return std::nullopt;
}

results_tuple parse(std::istream& input) {
    std::string line;
    std::getline(input, line);
    input.seekg(0);

    game found_game;
    spark_service found_service;
    std::vector<std::string> comments;

    if (line.rfind("<BLCMM", 0) == 0) {
        std::stringstream processed_xml;
        preprocess_blcmm_file(input, processed_xml);
        found_service = look_for_spark_service(input);

        pugi::xml_document doc{};
        auto res = doc.load(processed_xml, pugi::parse_default, pugi::encoding_latin1);
        if (res.status != pugi::status_ok) {
            throw blcmm_parser_error(res.description());
        }

        comments = extract_blcmm_comments(doc);
        found_game =  doc.select_node("/BLCMM/head/type/@name").attribute().as_string("");
        if (found_game == "") {
            found_game = std::nullopt;
        }
    } else if (line.rfind("#<", 0) == 0) {
        comments = extract_filtertool_comments(input);
        found_service = look_for_spark_service(input);
        found_game = std::nullopt;
    } else {
        comments = extract_generic_comments(input);
        found_service = look_for_spark_service(input);
        found_game = std::nullopt;
    }

    return {found_service, found_game, comments};
}
