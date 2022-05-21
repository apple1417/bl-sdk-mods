#ifndef __PARSER_H
#define __PARSER_H

#include <istream>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using spark_service = std::optional<int>;
using game = std::optional<std::string>;
using comments_list = std::vector<std::string>;

using results_tuple = std::tuple<spark_service, game, comments_list>;

/**
 * @brief Parse through a mod file and extract hotfix status, recommended game, and the first
 *        comment block.
 *
 * @param input The input stream to look through.
 * @return A tuple of the extracted data.
 */
results_tuple parse(std::istream& input);

#endif /* __PARSER_H */
