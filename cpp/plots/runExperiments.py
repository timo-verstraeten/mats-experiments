#!/usr/bin/env python

from __future__ import print_function
import argparse
import signal
import sys, json
import os
import errno
import subprocess
import time
import datetime
import multiprocessing, signal, time, subprocess, Queue
import itertools

# This script is used to concurrently execute experiment executables as
# specified by an input JSON file.
#
# The file specifies which files need to be run, and with which parameters. It
# also specifies a priority with which to execute the files, in order to
# increase the throughput.
#
# It additionally stores both output and statistics of the experiments.
#
# If an experiment has already been run, this script will not run it again,
# unless the executable as been updated more recently than the output.

# Queue containing the experiments to run
job_queue = multiprocessing.Queue()
# Queue containing the started processes (to ensure later that they are dead)
process_queue = multiprocessing.Queue()
# This class is used in order to concurrently process the experiments in groups
class WorkerProcess(multiprocessing.Process):
    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, self.end_my_worker)
        job_queue, process_queue = self._args

        while not job_queue.empty():
            try:
                print("Need to run " + str(job_queue.qsize()) + " experiments.")
                [exe, log_filename, self.statistics_filename] = job_queue.get(block=False)

                now = datetime.datetime.now().strftime("%H:%M:%S_%d-%m-%Y")
                print("[" + self.name + "] Now running: " + " ".join(exe) + " " + now)

                with open(self.statistics_filename, "w") as statistics_file:
                    statistics_file.write(now)

                self.start = time.time()

                with open(log_filename, "w") as log_file:
                    job = subprocess.Popen(exe, stdout=log_file, stderr=log_file)
                    process_queue.put(job)
                    job.wait()

                end = time.time()
                total_time = str(end - self.start)

                with open(self.statistics_filename, "a") as statistics_file:
                    statistics_file.write(" " + total_time)
                    statistics_file.write("\n")

                print("[" + self.name + "] Done. Took " + total_time + " seconds. (" + os.path.basename(self.statistics_filename) + ")")

            except Queue.Empty:
                pass

    def end_my_worker(self, signum, frame):
        # Still write what time we had here, so that the stats scripts can
        # check that it has ended (but will be marked as incomplete as no data
        # output will be produced).
        end = time.time()
        total_time = str(end - self.start)
        with open(self.statistics_filename, "a") as statistics_file:
            statistics_file.write(" " + total_time)
            statistics_file.write("\n")
        sys.exit(0)


# Helper functions
def mkdirMinusP(dirName):
    try:
        os.makedirs(dirName)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dirName):
            pass
        else:
            raise

def makeExeName(experiment, method):
    path = "../build/src/" + experiment + "_" + method + "_main"
    return os.path.abspath(path)

##################
##### PARSER #####
##################

parser = argparse.ArgumentParser()
parser.add_argument('experiments_file', type=str,
                    help="Json file containing the experiments to perform.")
parser.add_argument('N', type=int, nargs='?', default=4,
                    help="Number of processes to use")
parser.add_argument('-f', '--force', action='store_true',
                    help="Whether to force execution of all tests")
parser.add_argument('-e', '--experiment', nargs="*",
                    help="Which experiments to run, if not all")
parser.add_argument('-a', '--algorithm', nargs="*",
                    help="Which algorithms to run, if not all")
parser.add_argument('-t', '--test', action='store_true',
                    help="Just print which runs would have been made")
args = parser.parse_args()

# Loading JSON file
with open(args.experiments_file) as data_file:
    try:
        data = json.load(data_file)
    except:
        print("Could not load json from file", experiments_file)
        sys.exit(0)

experiments_file_folder = os.path.dirname(os.path.abspath(args.experiments_file))

# Sanity checks
folder = os.path.join(experiments_file_folder, data["folder"])
for e in data["experiments"]:
    for m in e["algorithms"]:
        exe = makeExeName(e["name"], m["name"])
        if not os.path.isfile(exe):
            print(exe, "not found!")
            sys.exit(1)

# We create a list of experiments to run.
#
# For each experiment, and for each algorithm, we cross-merge both global and
# local parameters.
#
# Note that if only global or local parameters are needed, there still needs to
# be at least one (possibly empty) parameter object for both experiment and
# algorithm, or there will not be anything to run.
#
# We then proceed to run the experiment files with the specified parameters,
# and we generate the appropriate output file.
#
# A given experiment is run only if the output file is missing, or if the
# experiment executable has been modified since the last creation of the output
# file.
jobs = []
mkdirMinusP(folder)
for e in data["experiments"]:
    if args.experiment is not None and e["name"] not in args.experiment:
        continue
    for m in e["algorithms"]:
        if args.algorithm is not None and m["name"] not in args.algorithm:
            continue

        exe = makeExeName(e["name"], m["name"])
        if "folder" in e:
            output_folder = folder + "/" + e["folder"] + "/" + m["name"]
        else:
            output_folder = folder + "/" + e["name"] + "/" + m["name"]
        logs_folder = output_folder + "/logs"
        statistics_folder = output_folder + "/statistics"

        mkdirMinusP(output_folder)
        mkdirMinusP(logs_folder)
        mkdirMinusP(statistics_folder)

        for global_parameter in e["global_parameters"]:
            for config in m["configs"]:
                # Merge parameters
                parameter_set = global_parameter.copy()
                parameter_set.update(config["parameters"])

                # Handle parameter vectors (cross of all possibilities)
                parameter_crosses = {}
                for k in parameter_set.keys():
                    if type(parameter_set[k]) is list:
                        parameter_crosses[k] = parameter_set[k]
                        del parameter_set[k]

                if len(parameter_crosses) == 0:
                    parameter_lists = [parameter_set.items()]
                else:
                    parameter_lists = []
                    k = parameter_crosses.keys()
                    combinations = itertools.product(*parameter_crosses.values())
                    for c in combinations:
                        new_list = parameter_set.items()
                        new_list += zip(k, c)
                        parameter_lists.append(new_list)


                # Create executable
                for parameter_list in parameter_lists:
                    parameter_list.sort()

                    filename = "_".join(["=".join([str(k), str(v)]) for k, v in parameter_list])

                    output_filename = output_folder + "/" + filename
                    log_filename = logs_folder + "/" + filename
                    statistics_filename = statistics_folder + "/" + filename

                    # Only run if not already, or the exe has been updated
                    if ( args.force or not os.path.isfile(output_filename) or
                            os.path.getmtime(exe) > os.path.getmtime(output_filename) ):

                        exe_call = []
                        if "command" in m:
                            exe_call.append(m["command"])
                        exe_call.append(exe)
                        exe_call.extend([p for t in parameter_list for p in ("--" + str(t[0]), str(t[1]))])
                        exe_call.extend(["--output", output_filename])

                        jobs.append((exe_call, log_filename, statistics_filename, config["priority"]))

# We run all the jobs in parallel
jobs.sort(key=lambda tup: tup[3], reverse=True)
if args.test:
    print("Need to run " + str(len(jobs)) + " experiments with " + str(args.N) + " threads.")
    for j in jobs:
        print(" ".join(j[0]))
    sys.exit(0)

for j in jobs:
    # Add jobs to the queue (remove useless priority here)
    job_queue.put(j[:3])

# If less jobs than allowed threads, only start the ones we need
jobs_number = min(args.N, job_queue.qsize())
# Finally run the work
print("Need to run " + str(job_queue.qsize()) + " experiments.")
print("Starting up " + str(jobs_number) + " jobs...")
workers = []
for i in range(jobs_number):
    tmp = WorkerProcess(args=(job_queue,process_queue))
    tmp.name = str(i)
    tmp.start()
    workers.append(tmp)

try:
    for worker in workers:
        worker.join()
except KeyboardInterrupt:
    print("Not accepting any more jobs")

    try:
        while not job_queue.empty():
            job_queue.get(block=False)
    except Queue.Empty:
        pass

    try:
        for worker in workers:
            worker.join()
        print("Finished pending jobs.")
    except KeyboardInterrupt:
        print("Killing pending jobs.")
        for worker in workers:
            worker.terminate()
            worker.join()

        while not process_queue.empty():
            try:
                subprocess = process_queue.get(block=False)
                subprocess.terminate()
            except Queue.Empty:
                pass
            except OSError as e: # Deleting already dead process
                pass
