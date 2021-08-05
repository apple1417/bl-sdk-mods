#pragma once

#include "parser.hpp"

#include <istream>

enum class enable_strategy {
    ALL,
    ANY,
    FORCE,
    NEXT
};

command_list handle_blcmm_file(std::istream& file, const command_names& cmd_names);
