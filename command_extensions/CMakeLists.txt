file(GLOB_RECURSE sources CONFIGURE_DEPENDS "file_parser/*.cpp" "file_parser/*.h")
pyunrealsdk_add_module(file_parser ${sources})

# Slight hack: we don't actually rely on pyunrealsdk, but using it's helper function sets up
# everything for us, so just redefine the link libraries here to not rely on it
set_property(TARGET file_parser PROPERTY LINK_LIBRARIES)
target_link_libraries(file_parser PRIVATE explicit_python pybind11::module)

target_link_libraries(file_parser PRIVATE pugixml)

install(
    TARGETS
        file_parser
    DESTINATION
        ${CMAKE_CURRENT_SOURCE_DIR}
)
