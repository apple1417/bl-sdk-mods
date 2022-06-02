#ifndef __BLCMM_H
#define __BLCMM_H

#include <iostream>
#include <stdexcept>

/**
 * @brief Custom exception thrown when BLCMM parsing fails
 */
class blcmm_parser_error : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

/**
 * @brief Preprocesses a BLCMM file into valid xml.
 * @note Leaves the stream directly after the line with the closing `</BLCMM>` tag.
 * @note BLCMM files use CP1252, if you need to translate encoding later. As all structure is ASCII,
 *       this function has no issues with files using these characters.
 *
 * @param blcmm_input A stream containing a blcmm file to use as input. This will be consumed.
 * @param xml_output A stream to output valid xml into.
 */
void preprocess_blcmm_file(std::istream& blcmm_input, std::ostream& xml_output);

/**
 * @brief Checks if a string is in a comma seperated list.
 * @note Intended to be used to check if a command is active in the current profile.
 *
 * @param value The value to search for.
 * @param list A comma seperated list
 * @return True if the value is found in the list, false otherwise.
 */
bool in_comma_seperated_list(const std::string& value, const std::string& list);

#endif /* __BLCMM_H */
