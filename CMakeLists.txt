cmake_minimum_required(VERSION 3.24)

project(willow2_sdk_mods)

add_subdirectory(.willow2-mod-manager EXCLUDE_FROM_ALL)
set_target_properties(pluginloader_no_proxy PROPERTIES EXCLUDE_FROM_ALL true)

file(GLOB_RECURSE subfolders RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "*/CMakeLists.txt")
foreach(cmakelists ${subfolders})
    if (${cmakelists} MATCHES "^\\.")
        continue()
    endif()

    get_filename_component(folder "${cmakelists}" DIRECTORY)
    message(STATUS "Including mod folder: ${folder}")
    add_subdirectory(${folder})
endforeach()
