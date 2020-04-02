cmake_minimum_required (VERSION 3.0)

project (Experiment)

add_definitions(
    -std=c++17 # Or -std=c++0x
    -Wall
    -Wextra
    # Other flags
)

# Set default cmake build type to release
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING
      "Choose the type of build, options are:
          Debug Release RelWithDebInfo MinSizeRel."
      FORCE)
endif()

# For additional Find library scripts
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${PROJECT_SOURCE_DIR}/cmake/Modules/")

# Add AIToolbox dependencies
find_package(Boost 1.53 COMPONENTS program_options REQUIRED)
include_directories(SYSTEM ${Boost_INCLUDE_DIRS})

find_package(Eigen3 3.2.92 REQUIRED)
include_directories(SYSTEM ${EIGEN3_INCLUDE_DIR})

# find_package(LpSolve REQUIRED)
# include_directories(${LPSOLVE_INCLUDE_DIR})

function (AddDependency name)
    add_subdirectory(${PROJECT_SOURCE_DIR}/deps/${name})
    include_directories(${PROJECT_SOURCE_DIR}/deps/${name}/include)
endfunction (AddDependency)

# Add AI-Toolbox folder
set(MAKE_MDP 1)
set(MAKE_FMDP 1)
AddDependency(AI-Toolbox)

# Add project directories
include_directories(${PROJECT_SOURCE_DIR}/include)
add_subdirectory(${PROJECT_SOURCE_DIR}/src)
