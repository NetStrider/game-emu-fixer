cmake_minimum_required(VERSION 3.16)

project(GameEmuFixer VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)

# FFTW3 for frequency analysis
pkg_check_modules(FFTW3F REQUIRED fftw3f)

# OpenAL for audio debugging
find_package(OpenAL REQUIRED)

# Threads for multi-threading
find_package(Threads REQUIRED)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${FFTW3F_INCLUDE_DIRS}
    ${OPENAL_INCLUDE_DIRS}
)

# Link directories
link_directories(
    ${FFTW3F_LIBRARY_DIRS}
)

# Compiler flags
add_compile_options(
    ${FFTW3F_CFLAGS_OTHER}
    -Wall
    -Wextra
    -O2
)

# Audio diagnostics library
add_library(audio_diagnostics STATIC
    src/audio_diagnostics/audio_monitor.cpp
    src/audio_diagnostics/audio_monitor.h
)

target_link_libraries(audio_diagnostics
    ${FFTW3F_LIBRARIES}
    ${OPENAL_LIBRARY}
    Threads::Threads
)

# Hunter audio analyzer (C++ wrapper for integration)
add_library(hunter_analyzer STATIC
    src/audio_analysis/hunter_analyzer.cpp
    src/audio_analysis/hunter_analyzer.h
)

target_link_libraries(hunter_analyzer
    audio_diagnostics
)

# Main diagnostic tool
add_executable(hunter_audio_diagnostics
    tools/hunter_diagnostics_main.cpp
)

target_link_libraries(hunter_audio_diagnostics
    audio_diagnostics
    hunter_analyzer
)

# Install targets
install(TARGETS hunter_audio_diagnostics
    DESTINATION bin
)

install(TARGETS audio_diagnostics hunter_analyzer
    DESTINATION lib
)

install(FILES
    src/audio_diagnostics/audio_monitor.h
    src/audio_analysis/hunter_analyzer.h
    DESTINATION include
)

# Python analysis tool installation
install(FILES
    src/audio_analysis/hunter_audio_analyzer.py
    DESTINATION bin
    PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)