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

This project uses a copy of the `AI-Toolbox` library, at the precise commit used
when the paper was published. The library webpage can be found at
`https://github.com/Svalorzen/AI-Toolbox`.  The documentation for the library
can be found there. The SHA used by this project is
`32f23155475491130166d8c79b01d54643e5a1d9`, but we made a minor fix for a
compiler error.

To compile the project just run these commands (please name the build folder
`build` as the experiment running/plotting code expects it like that):

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
