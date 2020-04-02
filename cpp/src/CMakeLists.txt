cmake_minimum_required (VERSION 3.0)

function (AddExperimentMDP name)
    set(exename ${name}_main)
    add_executable(${exename} ${exename}.cpp)
    target_link_libraries(${exename} AIToolboxMDP AIToolboxFMDP ${Boost_LIBRARIES} ${ARGN})
endfunction (AddExperimentMDP)

function (AddExperimentPOMDP name)
    set(exename ${name}_main)
    add_executable(${exename} ${exename}.cpp)
    target_link_libraries(${exename} AIToolboxMDP AIToolboxPOMDP ${Boost_LIBRARIES} ${ARGN})
endfunction (AddExperimentPOMDP)

function (AddExperimentFMDP name)
    set(exename ${name}_main)
    add_executable(${exename} ${exename}.cpp)
    target_link_libraries(${exename} AIToolboxMDP AIToolboxFMDP ${Boost_LIBRARIES} ${ARGN})
endfunction (AddExperimentFMDP)

add_library(ExperimentLibrary
    ./ThompsonSamplingBernoulliPolicy.cpp
    ./ThompsonSamplingPoissonPolicy.cpp
)
target_link_libraries(ExperimentLibrary AIToolboxMDP AIToolboxFMDP ${Boost_LIBRARIES})

# Experiments should be in the format:
#
# experimentname_methodname

AddExperimentFMDP(mines_mauce)
AddExperimentFMDP(mines_thompson)
AddExperimentFMDP(mines_thompsonb ExperimentLibrary)
AddExperimentFMDP(mines_scql)
AddExperimentFMDP(mines_llr)
AddExperimentMDP(mines_rnd)

AddExperimentFMDP(nodes_mauce)
AddExperimentFMDP(nodes_scql)
AddExperimentFMDP(nodes_llr)
AddExperimentFMDP(nodes_thompson)
AddExperimentMDP(nodes_rnd)
AddExperimentFMDP(nodes_thompsonb ExperimentLibrary)

AddExperimentMDP(nodesp_rnd)
AddExperimentFMDP(nodesp_scql)
AddExperimentFMDP(nodesp_llr)
AddExperimentFMDP(nodesp_mauce)
AddExperimentFMDP(nodesp_thompson)
AddExperimentFMDP(nodesp_thompsonp ExperimentLibrary)

find_package(PythonLibs 3 REQUIRED)
include_directories(SYSTEM ${PYTHON_INCLUDE_DIRS})

AddExperimentFMDP(wind_mauce ${PYTHON_LIBRARIES})
AddExperimentFMDP(wind_scql ${PYTHON_LIBRARIES})
AddExperimentFMDP(wind_llr ${PYTHON_LIBRARIES})
AddExperimentFMDP(wind_rnd ${PYTHON_LIBRARIES})
AddExperimentFMDP(wind_thompson ${PYTHON_LIBRARIES})
