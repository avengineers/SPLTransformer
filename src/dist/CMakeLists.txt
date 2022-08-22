# cmake project definition
cmake_minimum_required(VERSION 3.22.0)

set(VARIANT ${FLAVOR}/${SUBSYSTEM} CACHE STRING "Variant to build.")
set(BUILD_KIT prod CACHE STRING "Target Group to build.")

include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.cmake)

project(${VARIANT} C ASM)

# TODO: refactor link step to post build custom command
set(LINK_FILE_BASENAME link_out)
set(LINK_FILE_EXTENSION .elf)
set(LINK_HEX_FILE ${LINK_FILE_BASENAME}.hex)
set(LINK_MAP_FILE ${LINK_FILE_BASENAME}.map)
set(LINK_MDF_FILE ${LINK_FILE_BASENAME}.mdf)
list(APPEND LINK_TARGET_DEPENDS ${LINK_HEX_FILE})

include(tools/spl/cmake/spl.cmake)

spl_install_extension(epes_spl_extensions 0.12)

spl_run_conan()

epes_spl_extensions()

# TODO: we want this in spl.cmake, but CBD stuff in epes_spl_extensions forbids it.
include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)

# TODO: refactor/remove; we want to explicitly add includes where required
foreach(component_name ${COMPONENT_NAMES})
    target_include_directories(${component_name} PUBLIC ${target_include_directories__INCLUDES})
endforeach()
