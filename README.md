How To
======

Requirements
------------

The project requires:

- CMake
- Compiler support for C++17 (so at least `g++-7`)
- Boost library
- The Eigen matrix library 3.3.

Instructions
------------

First download the `AI-Toolbox` library via git submodules:

```
git submodule update --init --recursive
```

The library webpage can be found at `https://github.com/Svalorzen/AI-Toolbox`.
The documentation for the library can be found there.

Then compile the project (please name the build folder `build` as the experiment
running/plotting code expects it like that).

```
mkdir build
cd build
cmake ..
make
```

The `plots` folder contains some scripts to automatically run the experiments
and generate the output data. From there you can then generate the plots. Try
the `plots/runExperiments.sh` script first, with input the
`plots/experiments/experiments.json` file.

After the data has been generated, you can call the `plotGeneration.sh` script.
