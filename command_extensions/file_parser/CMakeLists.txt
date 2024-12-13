if(0)
# This CMakeLists can be used to compile the parser as a linux native module - useful for debugging

cmake_minimum_required(VERSION 3.24)
project(file_parser)

file(GLOB_RECURSE sources CONFIGURE_DEPENDS "*.cpp" "*.h")

add_subdirectory(../../.libs/pugixml subproject/pugixml EXCLUDE_FROM_ALL)
add_subdirectory(../../.willow2-mod-manager/libs/pyunrealsdk/libs/pybind11 subproject/pybind11 EXCLUDE_FROM_ALL)

pybind11_add_module(file_parser ${sources})

target_link_libraries(file_parser PRIVATE pugixml)

target_compile_features(file_parser PUBLIC cxx_std_20)
set_target_properties(file_parser PROPERTIES
    COMPILE_WARNING_AS_ERROR True
    INTERPROCEDURAL_OPTIMIZATION True
    EXPORT_COMPILE_COMMANDS True
    PREFIX ""
)

target_compile_definitions(file_parser PUBLIC PYBIND11_DETAILED_ERROR_MESSAGES=1)

install(
    TARGETS
        file_parser
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)

endif()
