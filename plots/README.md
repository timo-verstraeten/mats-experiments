How to Run the Experiments
==========================

The list of experiments to run is contained in the file `experiments.json` in
the `experiments` folder. It contains a list of executables and the parameters
with which they must be run.

The file can be given as input to the `runExperiments.py` script. The script
will generate automatically, based on the information contained in the `json`
file, a series of folders - one per each separate experiment, and inside one per
each method. Each folder will contain:

- A `log` folder containing all outputs to `stdout` and `stderr` of all the runs
  - one for each set of parameters.
- A `statistics` folder containing, for each run, a file with the number of
  seconds that the particular run took to complete.

In particular, the executables for the experiments themselves create a file
containing the average rewards over all episodes/timestep.

Note that an experiment will be run ONLY IF the output file of the experiments
does not exist, or the executable of the experiment has been updated more
recently than the last generated output for it. This avoids duplicating work
when unneeded.

Plotting
--------

The output files can be given to the `plotResult.py` script, which will create
an appropriate plot of the input files.

The script `plotGeneration.sh` creates a number of these plots from the data
created by the `experiments.json` file.
