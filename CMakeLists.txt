project(shad-cpp0)

cmake_minimum_required(VERSION 3.8)

set(CMAKE_CXX_STANDARD             17)
set(CMAKE_MODULE_PATH              "${CMAKE_SOURCE_DIR}/cmake")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
set(CMAKE_EXPORT_COMPILE_COMMANDS  ON)

find_package(Catch REQUIRED)
find_package(PNG)
find_package(JPEG)

find_package(Poco QUIET COMPONENTS Foundation Net JSON)
if (NOT Poco_FOUND)
  message(STATUS "Seems like POCO is not installed on your machine.")
  message(STATUS "Tasks that depend on POCO are disabled.")
endif()

find_package(PythonLibs 3 QUIET)
if (NOT PythonLibs_FOUND)
  message(STATUS "python3 libraries not found. Python tasks are disabled.")
endif()

include(cmake/TestSolution.cmake)
include(cmake/BuildFlags.cmake)
include_directories(util)

add_subdirectory(find-last)
add_subdirectory(local-max)
add_subdirectory(remove-if)
add_subdirectory(partition)
add_subdirectory(fold)
add_subdirectory(functors)