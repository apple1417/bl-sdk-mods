#ifndef FILE_PARSER_MATCHER_H
#define FILE_PARSER_MATCHER_H

#include "pch.h"

namespace ce {

// Traits class which compares case-insensitively
struct CaseInsensitiveTraits : public std::char_traits<char> {
    static bool eq(char chr_a, char chr_b);
    static bool lt(char chr_a, char chr_b);
    static int compare(const char* chr_a, const char* chr_b, size_t n);
};
struct CaseInsensitiveString : public std::basic_string<char, CaseInsensitiveTraits> {
    using std::basic_string<char, CaseInsensitiveTraits>::basic_string;
};
struct CaseInsensitiveStringView : public std::basic_string_view<char, CaseInsensitiveTraits> {
    using std::basic_string_view<char, CaseInsensitiveTraits>::basic_string_view;

    CaseInsensitiveStringView(std::string_view str);
    bool operator==(std::string_view str) const;
};

/**
 * @brief Updates the commands being matched.
 *
 * @param commands The set of commands to match.
 */
void update_commands(std::vector<CaseInsensitiveString>& commands);

/**
 * @brief Adds an individual new command to the list.
 *
 * @param cmd The command to add. May have leading/trailing whitespace.
 */
void add_new_command(CaseInsensitiveStringView cmd);

struct CommandMatch {
    std::string_view cmd;
    py::object py_cmd;
    py::object line;
    Py_ssize_t cmd_len;

    /**
     * @brief Attempts to match a line to a command.
     *
     * @param line The line to match.
     */
    CommandMatch(std::string_view line);

    /**
     * @brief Checks if this match was successful.
     *
     * @return True on successful match.
     */
    operator bool() const;
};

}  // namespace ce

#endif /* FILE_PARSER_MATCHER_H */
