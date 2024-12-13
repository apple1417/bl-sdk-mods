#ifndef LINE_PARSER_H
#define LINE_PARSER_H

#include "pch.h"
#include "matcher.h"

namespace ce {

/**
 * @brief Parses through a file stream line by line, collecting all matching commands.
 *
 * @return A list of command matches
 */
std::vector<CommandMatch> parse_file_line_by_line(std::istream& stream);

}  // namespace ce

#endif /* FILE_PARSER_BLCM_PARSER_H */
