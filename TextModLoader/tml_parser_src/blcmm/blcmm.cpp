#include "blcmm.hpp"

#include <iostream>
#include <string>
#include <optional>

static const std::string FILTERTOOL_WARNING = "#<!!!You opened a file saved with BLCMM in FilterTool. Please update to BLCMM to properly open this file!!!>";

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

void preprocess_blcmm_file(std::istream& blcmm_input, std::ostream& xml_output) {
    std::optional<std::string> root_opening_tag = std::nullopt;
    std::optional<std::string> root_closing_tag = std::nullopt;
    auto root_tag_nest_count = 0;

    for (std::string line; std::getline(blcmm_input, line); ) {
        auto tag_start = line.find_first_of('<');
        if (tag_start == std::string::npos) {
            throw blcmm_parser_error("Failed to parse line (couldn't find inital tag): " + line);
        }

        // Ignore the filtertool warning
        auto filtertool_start = line.find(FILTERTOOL_WARNING, tag_start - 1);
        if (filtertool_start != std::string::npos && (filtertool_start + 1) == tag_start) {
            continue;
        }

        auto tag_name_end = line.find_first_of("> \t", tag_start);
        if (tag_name_end == std::string::npos) {
            throw blcmm_parser_error("Failed to parse line (inital tag doesn't close): " + line);
        }

        // Includes the starting char(s), excludes the ending char
        std::string tag_name = line.substr(tag_start, tag_name_end - tag_start);

        xml_output << tag_name;
        xml_output << line[tag_name_end];

        if (!root_opening_tag.has_value()) {
            // Just assume the first tag is opening, the XML parsing will fail if it's not anyway
            root_opening_tag = tag_name;
            root_closing_tag = "</" + tag_name.substr(1);
            root_tag_nest_count++;
        } else {
            // Keep track of nested tags of the same type as the root
            if (tag_name == root_opening_tag.value()) {
                root_tag_nest_count++;
            } else if (tag_name == root_closing_tag.value()) {
                root_tag_nest_count--;
            }

            // If we make it back to 0, we've finished
            if (root_tag_nest_count == 0) {
                // Add the closing `>` if there's whitespace
                if (line[tag_name_end] != '>') {
                    xml_output << '>';
                }
                break;
            }
        }

        auto content_start = tag_name_end + 1;

        // If we have attributes to parse
        if (line[tag_name_end] != '>') {
            auto tag_body_section_start = content_start;
            while (true) {
                // Grab all characters up to the next attribute value, or the end of the tag
                auto tag_body_section_end = line.find_first_of("\">", tag_body_section_start);
                if (tag_body_section_end == std::string::npos) {
                    throw blcmm_parser_error(
                        "Failed to parse line (inital tag doesn't close): " + line
                    );
                }
                xml_output << line.substr(
                    tag_body_section_start,
                    tag_body_section_end - tag_body_section_start + 1
                );

                // We found the end of the tag
                if (line[tag_body_section_end] == '>') {
                    content_start = tag_body_section_end + 1;
                    break;
                }

                // We have an attribute value - find where it ends
                auto attr_val_end = tag_body_section_end;
                do {
                    attr_val_end = line.find_first_of('"', attr_val_end + 1);
                    if (attr_val_end == std::string::npos) {
                        throw blcmm_parser_error(
                            "Failed to parse line (attribute value doesn't close): " + line
                        );
                    }
                } while (line[attr_val_end - 1] == '\\');

                // Escape the attribute value
                for (size_t i = tag_body_section_end + 1; i < attr_val_end; i++) {
                    if (line[i] == '\\' && line[i + 1] == '"') {
                        continue;
                    }
                    put_xml_escaped(line[i], xml_output);
                }
                xml_output << '"';

                tag_body_section_start = attr_val_end + 1;
            }
        }

        // If the tag was self closing, the line must be over
        if (line[content_start - 2] == '/') {
            continue;
        }

        // Find the closing tag and escape all text content
        auto closing_tag_str = (
            "</" + line.substr(tag_start + 1, tag_name_end - tag_start - 1)
        );
        auto closing_tag_start = line.rfind(closing_tag_str);

        // Nothing to do if it's an opening nested tag
        // This is the case if we can't find the closing tag after the start of the content
        // (We may find it before the start of the content if it's in an attribute)
        if (closing_tag_start != std::string::npos && closing_tag_start >= content_start) {
            for (size_t i = content_start; i < closing_tag_start; i++) {
                put_xml_escaped(line[i], xml_output);
            }

            xml_output << closing_tag_str;
            xml_output << ">";
        }
    }

    if (blcmm_input.fail()) {
        if (blcmm_input.eof()) {
            if (root_opening_tag.has_value()) {
                throw blcmm_parser_error("IO Error while reading input (eof)");
            }
            // If we got EOF but didn't have an opening tag, it's an empty file, exit without error
        } else {
            throw blcmm_parser_error("IO Error while reading input");
        }
    }

    if (xml_output.fail()) {
        throw blcmm_parser_error("IO Error while writing output");
    }
}

bool in_comma_seperated_list(const std::string& value, const std::string& list) {
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
