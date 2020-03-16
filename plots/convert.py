#!/usr/bin/env python

import sys
import math
import os
import shutil
import subprocess
import errno

if len(sys.argv) < 3:
    print("usage: " + sys.argv[0] + " experiment_folder output_folder")
    sys.exit(0)

experiment_folder = sys.argv[1]
output_folder = sys.argv[2]

if not os.path.isdir(experiment_folder):
    print("Input experiment folder does not exist")
    sys.exit(1)

if experiment_folder == output_folder:
    print("Can't use same folder for input and output")
    sys.exit(1)

# Helper functions
def mkdirMinusP(dirName):
    try:
        os.makedirs(dirName)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dirName):
            pass
        else:
            raise

def numChoice(minv, maxv):
    while True:
        print("Please select a number in [" + str(minv) + ", " + str(maxv) + "]: "),
        choice = raw_input()
        if choice == "q":
            sys.exit(0)
        try:
            choice = int(choice)
            if choice >= minv and choice <= maxv:
                break
            else:
                print("Value is out of bounds, please try again.")
        except ValueError:
            print("Could not convert input to number.")
    return choice

if os.path.isdir(output_folder):
    print(output_folder + " already exists; want to delete? [Y*/n]: "),
    choice = raw_input().lower()
    if choice in ["y", "Y", "yes", ""]:
        shutil.rmtree(output_folder)
    else:
        print("Aborting...")
        sys.exit(0)

methods = [m for m in os.listdir(experiment_folder) if os.path.isdir(os.path.join(experiment_folder, m))]
all_method_files = {}
all_method_count = 0

for m in methods:
    method_folder = os.path.join(experiment_folder, m)

    method_files = [f for f in os.listdir(method_folder) if os.path.isfile(os.path.join(method_folder, f))]
    if len(method_files) > 0:
        all_method_count += len(method_files)
        all_method_files[m] = method_files

if all_method_count < 2:
    print("Nothing to do...")
    sys.exit(0)

all_method_dict = {}

methods = all_method_files.keys()

if len(methods) == 1:
    choice = 0
else:
    counter = 0
    for m in methods:
        print(str(counter) + ": " + m)
        counter += 1
    choice = numChoice(0, len(methods)-1)

m = methods[choice]
files = all_method_files[m]

print("")
print("[" + m + "]")
if len(files) == 1:
    choice = 0
else:
    counter = 0
    for f in files:
        print(str(counter) + ": " + f)
        counter += 1

    choice = numChoice(0, len(files)-1)

base_file = os.path.join(experiment_folder, m, files[choice])

mkdirMinusP(output_folder)
for mm in methods:
    if mm == m and len(files) == 1:
        continue
    mkdirMinusP(os.path.join(output_folder, mm))
    for f in all_method_files[mm]:
        transformed_file = os.path.join(experiment_folder, mm, f)
        if transformed_file == base_file:
            continue
        output_file = os.path.join(output_folder, mm, f)
        subprocess.call(["./transform.py", "-", base_file, transformed_file, output_file])

