cmake_minimum_required(VERSION 3.10)
project(SumatraPDF_Harness)

set(CMAKE_CXX_STANDARD 17)

# Create the mock libmupdf library
add_library(mupdf_mock STATIC mupdf_mock.c)

# Create the harness executable
add_executable(harness harness.cpp)

# Link the mock library to the harness
target_link_libraries(harness PRIVATE mupdf_mock)
