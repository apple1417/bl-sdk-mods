#ifndef FILE_PARSER_BLCM_PARSER_H
#define FILE_PARSER_BLCM_PARSER_H

#include "pch.h"
#include "matcher.h"

namespace ce {

/**
 * @brief The various enable strategies that can be used in a BLCMM file.
 */
enum class EnableStrategy { ALL, ANY, FORCE, NEXT };

/**
 * @brief Parses through a blcmm file stream, collecting all matching commands.
 *
 * @return A list of enabled command matches
 */
std::vector<CommandMatch> parse_blcmm_file(std::istream& stream);

}  // namespace ce

#endif /* FILE_PARSER_BLCM_PARSER_H */
