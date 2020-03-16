#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import errno
import shutil
import subprocess
import json
import datetime

if len(sys.argv) < 2:
    print("Print time statistics and generate experiments json.\n")
    print("usage: " + sys.argv[0] + " folder [experiments ...] [--partition=N [--json=filename]]")
    print(
"""
This file can be used to automatically extract the statistics for certain
experiments, and if needed to automatically generate a somewhat balanced json
made of N partitions. The partitions will be made so that they are as close to
each other as possible in terms of time, which should reduce the amount of
overall time. If a file is not specified, the script just shows how the
partitions would have been made.
""")
    sys.exit(0)

# Parsing a required parameter
def readName(i, label):
    if i >= len(sys.argv):
        print("Couln't read " + label)
        sys.exit(1)

    name = sys.argv[i]
    if name.startswith("-"):
        print("String passed for " + label + " is invalid.")
        sys.exit(1)

    return name, i+1

# Parsing an optional parameter
def tryReadName(i, label):
    if i >= len(sys.argv):
        print("Couln't read " + label)
        sys.exit(1)

    name = sys.argv[i]
    if name.startswith("-"):
        return False, "", i+1

    return True, name, i+1

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
folder, i = readName(i, "folder")
global_experiments = []
partitioning = (False, 0)
partitioning_output = None

methods = {}
while i < len(sys.argv):
    # Extract all experiment params, and check whether we need to do
    # partitioning and/or json production.
    valid, experiment, i = tryReadName(i, "experiment")
    if valid:
        global_experiments.append(experiment)
    else:
        option = sys.argv[i-1]
        part_option = "--partition="
        json_option = "--json="
        if option.startswith(part_option):
            partitioning = (True, int(option[len(part_option):]))
        elif option.startswith(json_option):
            if not partitioning[0]:
                print("Json cannot be produced with no partitioning")
                sys.exit(1)
            partitioning_output = option[len(json_option):]
        else:
            print("Unrecognized option: " + option)
            sys.exit(1)

# If no experiments were passed, glob up all available
if len(global_experiments) > 0:
    experiments = global_experiments
else:
    experiments = [e for e in os.listdir(folder) if os.path.isdir(os.path.join(folder, e))]

statistics = {}
for e in experiments:
    statistics[e] = {}
    experiment_folder = os.path.join(folder, e)

    # Check which methods are available for this experiment
    methods = [m for m in os.listdir(experiment_folder) if os.path.isdir(os.path.join(experiment_folder, m))]

    for m in methods:
        statistics[e][m] = []
        method_folder = os.path.join(experiment_folder, m)
        statistics_folder = os.path.join(method_folder, "statistics")

        # All files in the stats folder
        method_files = [f for f in os.listdir(statistics_folder) if os.path.isfile(os.path.join(statistics_folder, f))]
        for f in method_files:
            complete = False
            # Check if there's actually data for this (maybe we deleted it?)
            if f in os.listdir(method_folder):
                complete = True
            file_options = f.split("_")
            with open(os.path.join(statistics_folder, f)) as stat_file:
                # The file either contains the start date, or that plus the
                # duration. We only care about the last element in both cases.
                content = stat_file.read().strip().split()
                statistics[e][m].append((file_options, complete, content[-1]))


if len(statistics) == 0:
    print("No statistics to show")
    sys.exit(0)

for e in experiments:
    print("Experiment [" + e + "]")
    for m, stats in statistics[e].items():
        print("    Algorithm [" + m + "]")
        for stat in stats:
            inputstring = "%-20s" * len(stat[0])
            unit = " seconds"
            try:
                duration = float(stat[-1])
                options = "" if stat[1] else " (incomplete)"
                unit = " seconds"
            except ValueError:
                start = datetime.datetime.strptime(stat[-1], "%H:%M:%S_%d-%m-%Y")
                now = datetime.datetime.now()
                duration = (now - start).total_seconds()
                options = " (running, "
                options += "complete?" if stat[1] else "incomplete"
                options += ")"

            # If more than 5 minutes
            if duration > 120.0:
                duration = duration / 60.0
                unit = " minutes"
            # If more than 2 hours
            if duration > 120:
                duration = duration / 60.0
                unit = " hours"

            durationstr = "{0:.4f}".format(duration) + unit + options
            print("        " + (inputstring % tuple(stat[0])) + "= " + durationstr)

if partitioning[0]:
    partitions = partitioning[1]

    overall_list = []
    for e in statistics:
        for m in statistics[e]:
            for stat in statistics[e][m]:
                element = [e, m]
                element.extend(stat[0])
                element.append(stat[-1])
                overall_list.append(element)

    sums = [0] * partitions
    solution = [[] for x in xrange(partitions)]

    overall_list.sort(key=lambda t: t[-1], reverse=True)

    while len(overall_list) > 0:
        val, idx = min((val, idx) for (idx, val) in enumerate(sums))
        element = overall_list.pop(0)
        solution[idx].append(element)
        sums[idx] += element[-1]

    print("\n\n")
    for i in xrange(partitions):
        print('- Partition' + str(i+1))
        for element in solution[i]:
            inputstring = "%-12s %-12s"
            inputstring += "%-20s" * (len(element) - 3)
            print(inputstring % tuple(element[:-1]) + "= {0:.4f}".format(element[-1]))
        print("Sum: " + str(sums[i]) + "\n")

    if partitioning_output is not None:
        data = {}
        data["folder"] = "./results"
        data["experiments"] = [[] for x in xrange(partitions)]
        for i in xrange(partitions):
            partition = {}
            for e in solution[i]:
                if not e[0] in partition:
                    partition[e[0]] = {}
                if not e[1] in partition[e[0]]:
                    partition[e[0]][e[1]] = []
                partition[e[0]][e[1]].append(e[2:-1])

            for e, v in partition.items():
                json_partition = {}
                json_partition["name"] = e
                json_partition["global_parameters"] = [{}]
                json_partition["algorithms"] = []
                json_methods = []
                for m, vv in v.items():
                    json_method = {}
                    json_method["name"] = m
                    json_method["parameters"] = []
                    for params in vv:
                        json_params = {}
                        for p in params:
                            k, v = p.split("=")
                            json_params[k] = v
                        json_method["parameters"].append(json_params)
                    json_partition["algorithms"].append(json_method)
                data["experiments"][i].append(json_partition)

        dump = json.dumps(data, indent=4, sort_keys=True)
        with open(partitioning_output, "w+") as partitioning_file:
            partitioning_file.write(dump)
