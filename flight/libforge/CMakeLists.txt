# libforge: portable C99 payload core. Standalone build + tests:
#   cmake -S flight/libforge -B build/libforge && cmake --build build/libforge && ctest --test-dir build/libforge
cmake_minimum_required(VERSION 3.16)
project(libforge C)
set(CMAKE_C_STANDARD 99)
add_compile_options(-Wall -Wextra -Werror -pedantic)
add_library(forge STATIC src/forge.c)
target_include_directories(forge PUBLIC include)
enable_testing()
add_executable(test_libforge test/test_libforge.c)
target_link_libraries(test_libforge forge)
target_include_directories(test_libforge PRIVATE test)
add_test(NAME libforge COMMAND test_libforge)
