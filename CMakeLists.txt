cmake_minimum_required(VERSION 3.14)
project(PokemonSimulator)
set(CMAKE_CXX_STANDARD 17)
include(CTest)

# ============================================================
# Platform detection
# ============================================================
if(WIN32)
    message(STATUS "Building on Windows")
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
else()
    message(STATUS "Building on Linux/Unix")
endif()

# Find packages — nlohmann_json (header-only, try bundled fallback)
find_package(nlohmann_json QUIET)
if(NOT nlohmann_json_FOUND)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third_party/json/single_include/nlohmann/json.hpp")
        message(STATUS "Using bundled nlohmann_json")
        add_library(nlohmann_json INTERFACE)
        target_include_directories(nlohmann_json INTERFACE
            "${CMAKE_CURRENT_SOURCE_DIR}/third_party/json/single_include")
        add_library(nlohmann_json::nlohmann_json ALIAS nlohmann_json)
    else()
        message(FATAL_ERROR "nlohmann_json not found. Install via vcpkg or clone to third_party/json/")
    endif()
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party/cpp-httplib)

# SQLite3 (amalgamation)
add_library(sqlite3 STATIC third_party/sqlite3/sqlite3.c)
target_include_directories(sqlite3 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/sqlite3)
target_compile_definitions(sqlite3 PRIVATE SQLITE_THREADSAFE=1)
if(MSVC)
    target_compile_options(sqlite3 PRIVATE /wd4996 /wd4146)
endif()

# Source files
file(GLOB SOURCES CONFIGURE_DEPENDS src/*.cpp)
file(GLOB SOURCES_BATTLE CONFIGURE_DEPENDS
    src/battle/*.cpp
    src/IO/*.cpp
    src/tests/*.cpp
)

# Ensure critical battle data sources are always linked even when CMake glob cache is stale.
list(APPEND SOURCES_BATTLE
    src/IO/MoveData.cpp
    src/tests/MoveTestRunner.cpp
    src/IO/AbilityData.cpp
    src/IO/ItemData.cpp
    src/tests/ItemTestRunner.cpp
    src/IO/BattleSession.cpp
    src/battle/GameRegistry.cpp
)

# Battle core library (server-side reusable logic)
add_library(battle_core ${SOURCES_BATTLE})
target_include_directories(battle_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(battle_core
    nlohmann_json::nlohmann_json
    sqlite3
)
# Executable
add_executable(PokemonSimulator ${SOURCES})

# Link libraries
target_link_libraries(PokemonSimulator
    battle_core
    nlohmann_json::nlohmann_json
)

# Windows: set default output directory for multi-config generators (MSVC)
if(MSVC)
    set_target_properties(PokemonSimulator PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Release"
        RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/Debug"
    )
endif()

if(BUILD_TESTING)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
    )
    if(WIN32)
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    else()
        set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    endif()
    FetchContent_MakeAvailable(googletest)

    add_executable(PokemonSimulatorTests
        tests/battle_data_test.cpp
    )

    target_include_directories(PokemonSimulatorTests PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
    )

    target_link_libraries(PokemonSimulatorTests
        battle_core
        nlohmann_json::nlohmann_json
        GTest::gtest_main
    )

    include(GoogleTest)
    gtest_discover_tests(PokemonSimulatorTests)
endif()
