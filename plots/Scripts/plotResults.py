#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import errno
import shutil
import subprocess
import re

# This script is used in order to create a single PNG file containing the plot
# of the specified methods.
#
# The data used to create the plots must already exist, and be in a folder hierarchy
# that this script understands. To sum it up:
#
# - This file will look in the directory [folder/experiment]
# - For each method to plot, it will look into [folder/experiment/method]. If
#   no methods are specified, all folders found are used.
# - Inside each method folder, it will look for all files which contain options
#   which match the ones specified by the user. If no options are specified, all
#   files will match.
#
# This script makes use of the makeGnuplotScript.sh file, which you may need to
# modify in order to change GnuPlot behaviour.

# NOTE: ADDITIONAL PARAMETERS
#
# To avoid complicating the script parsing too much, since it's already pretty
# bad, we offer a couple of options here in forms of variables.
use_title = 0                   # Whether to add a title to the plot.
title_name = ""                 # Title name (if unspecified, the experiment)
use_subtitle_parameters = 0     # Whether to add a subtitle containing all common flags for all experiments
use_line_parameters = 1         # Whether to add line-specific parameters to the legend
default_plotting = 1            # Whether to default to cumulative (1) or immediate (0) plotting

if len(sys.argv) < 2:
    print("usage: " + sys.argv[0] + " [--output=file] [--xlim=na] [--xtics=na] [--ylim=na] [--cumulative=0/1-na] folder experiment [--name=value ...] [method [--name=value ...] [method [--name=value ...] ...]]")
    sys.exit(0)

def mkdirMinusP(dirName):
    """ This function creates the folder specified, even if nested. """
    try:
        os.makedirs(dirName)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dirName):
            pass
        else:
            raise

def readName(i, label):
    if i >= len(sys.argv):
        print("Couln't read " + label)
        sys.exit(1)

    name = sys.argv[i]
    if name.startswith("-"):
        print("String passed for " + label + " is invalid.")
        sys.exit(1)

    return name, i+1

def readFlags(i):
    flags = {}
    while i < len(sys.argv) and sys.argv[i].startswith("--"):
        flag = sys.argv[i][2:]
        flag_kv = flag.split("=")
        if (len(flag_kv) != 2 or
            len(flag_kv[0]) < 1 or len(flag_kv[1]) < 1):
            print("Option " + flag + " is invalid.")
            sys.exit(1)
        flags[flag_kv[0]] = flag_kv[1]
        i += 1
    return flags, i

i = 1
globalFlags, i = readFlags(i)
if "output" in globalFlags:
    output = globalFlags["output"]
else:
    output = None

if "cumulative" in globalFlags:
    default_plotting = globalFlags["cumulative"]

def getFileFlags(filename):
    tmp = filename.split("_")
    flags = set()
    curr_flag = ""
    for t in tmp:
        curr_flag += t
        if "=" in curr_flag:
            flags.add(curr_flag)
            curr_flag = ""
        else:
            curr_flag += "_"
    return flags

folder, i = readName(i, "folder")
experiment, i = readName(i, "experiment")
experiment_flags, i = readFlags(i)
experiment_folder = os.path.join(folder, experiment)

# Read the methods to plot, and the flags to use for each one.
methods_order = []
methods_plot_name = {}
methods_flags = {}
while i < len(sys.argv):
    method, i = readName(i, "method")
    method_flags, i = readFlags(i)

    # If we have passed the method in the form of '[ab,cd]' then the first is
    # the name of the experiment, the second is the name we want on the plot
    if method[0] == '[':
        method = method[1:-1]
        method = method.split(',')
        method_name = method[1]
        method = method[0]
    else:
        method_name = method
    methods_flags[method] = method_flags
    methods_plot_name[method] = method_name
    methods_order.append(method)

if len(methods_flags) == 0:
    methods_flags = {m: {} for m in os.listdir(experiment_folder) if os.path.isdir(os.path.join(experiment_folder, m))}
    methods_plot_name = {m : m for m in methods_flags.keys()}
    methods_order = methods_flags.keys()

if len(methods_flags) == 0:
    print("Nothing to plot")
    sys.exit(1)

# Array of tuples
# Each tuple is files to read, the folder where they are, and the method name
files_to_plot = []
for m in methods_order:
    param = methods_flags[m]
    data_folder = os.path.join(experiment_folder, m)
    if not os.path.isdir(data_folder):
        print("Missing folder for method " + m + "; skipping...")
        continue
    options = param.copy()
    options.update(experiment_flags)
    options_list = []
    for kv in options.items():
        options_list.append([kv[0] + "=" + v for v in kv[1].split(",")])

    method_files = [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]
    for f in method_files:
        file_options = f.split("_")
        if all(any(value in file_options for value in options) for options in options_list):
            files_to_plot.append((f, data_folder, m))

if len(files_to_plot) == 0:
    print("No files match the specified options")
    sys.exit(0)

plotTmpDir = "/tmp/plotDir"
mkdirMinusP(plotTmpDir);

common_flags = getFileFlags(files_to_plot[0][0])
for f in files_to_plot:
    common_flags = common_flags.intersection(getFileFlags(f[0]))

common_flags_list = list(common_flags)
common_flags_list.sort()

# Array of array
# Each is file, label, cumulative (as per makeGnuplotScript)
fileLabels = []
for f in files_to_plot:
    params = getFileFlags(f[0])
    new_params = [p for p in params if p not in common_flags]

    # This is the name of the file we are going to create (by copying the
    # original to plot) and that gnuplot is going to read
    newFilename = f[2]
    if len(new_params) > 0:
        newFilename += " " + ",".join(new_params)

    # File, label, cumulative
    newElem = []

    # Filename to pass to gnuplot
    newElem.append(newFilename)

    # Name to put on the plot
    name = methods_plot_name[f[2]]
    if use_line_parameters:
        newElem.append(name + " " + ",".join(new_params))
    else:
        newElem.append(name)

    # Whether to use cumulative data or per-timestep data
    newElem.append(str(default_plotting))

    # Add to lines to plot
    fileLabels.append(newElem)

    # Copy the file to plot with the correct name
    shutil.copyfile(os.path.join(f[1], f[0]), os.path.join(plotTmpDir, newFilename))

def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval

def natural_keys(text):
    text = text[1]
    return [ atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text) ]
fileLabels.sort(key=natural_keys)
fileLabels = [item for elem in fileLabels for item in elem]

title = ""
if use_title:
    title = experiment
    if title_name:
        title = title_name

    # Add common flags to the title.
    if use_subtitle_parameters and len(common_flags_list) > 0:
        title += '\\\\n{/*0.75' + ",".join(common_flags_list) + "}"

# We assume we're together with the makeGnuplotScript.sh file
dir_path = os.path.dirname(os.path.realpath(__file__))
execall = [dir_path + "/makeGnuplotScript.sh"]
if output is not None:
    cwd = os.getcwd()
    output_filename = os.path.join(cwd, output)
    execall.append(output_filename)
else:
    execall.append("term")
if "xlim" in globalFlags:
    execall.append(globalFlags["xlim"])
else:
    execall.append("na")
if "xtics" in globalFlags:
    execall.append(globalFlags["xtics"])
else:
    execall.append("na")
if "ylim" in globalFlags:
    execall.append(globalFlags["ylim"])
else:
    execall.append("na")
execall.append(title)
execall.extend(fileLabels)
print(execall)
# Create plot script
with open(os.path.join(plotTmpDir, "plot"), "w+") as plotFile:
    subprocess.call(execall, stdout=plotFile)

with open(os.path.join(plotTmpDir, "plot"), "r") as plotFile:
    print(plotFile.read())
# Plot
subprocess.call(["gnuplot","-p","plot"], cwd=plotTmpDir)

shutil.rmtree(plotTmpDir)
