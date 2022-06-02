#ifndef __PARSE_H
#define __PARSE_H

#include <istream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using command_list = std::vector<std::pair<std::string, std::string>>;
using command_names = std::unordered_set<std::string>;

/**
 * @brief The various enable strategies that can be used in a BLCMM file.
 */
enum class enable_strategy {
    ALL,
    ANY,
    FORCE,
    NEXT
};

/**
 * @brief Parses through a stream looking for custom commands.
 * @note Attempts parse a BLCMM file, falls back to line by line based parsing if not recognised.
 *
 * @param stream A stream containing the file to parse.
 * @param cmd_names A set of valid command names, all in lowercase.
 * @return A list of enabled commands within the file.
 */
command_list parse(std::istream& stream, const command_names& cmd_names);


#endif /* __PARSE_H */
