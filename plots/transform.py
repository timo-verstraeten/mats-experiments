#!/usr/bin/env python

import sys
import math
import os
import errno

if len(sys.argv) < 3:
    print("usage: " + sys.argv[0] + " op input_file [input_file ...] output_file")
    sys.exit(1)

del sys.argv[0]

output = sys.argv[-1]
del sys.argv[-1]

validops = ['+', '-', '-m', 'gt0']
binaryops = ['+', '-']

if sys.argv[0] not in validops:
    print("Operation argument is none of " + ", ".join(validops))
    sys.exit(1)
op = sys.argv[0]
del sys.argv[0]

files = sys.argv
if len(files) < 1:
    print("No input files passed.")
    sys.exit(1)
if op not in binaryops and len(files) != 1:
    print("Only one input file allowed for unary transformations.")
    sys.exit(1)

# Returns an array of the parsed file containing, for each line, an array with
#
# - immediate mean
# - cumulative mean
# - immediate variance
# - cumulative variance
#
# We transform here stds in variances to ease operations.
def parseFile(filename, expectedLength = 0):
    with open(filename, 'r') as file:
        # read a list of lines into data
        stringData = file.readlines()
    print(stringData[-1])

    parsedData = []
    for i in range(len(stringData)):
        # Parse values as floats (skip index)
        x = [float(v) for v in stringData[i].split()[1:]]
        # Std -> Variance
        x[2:] = [v ** 2 for v in x[2:]]
        # Append with index again
        parsedData.append(x)

    if expectedLength != 0 and len(parsedData) != expectedLength:
        print("The length of file " + filename + " is " + str(len(stringData)) +
              ", different from the expected " + str(expectedLength))
        sys.exit(1)

    return parsedData

def firstPass(op, i, lhs, rhs):
    # Here we:
    # - Accumulate means
    # - Accumulate variances
    if op == '+':
        return [lv + rv for lv, rv in zip(lhs, rhs)]

    # Here we:
    # - Subtract the new means from the old data.
    # - Accumulate variances
    elif op == '-':
        return ([lv - rv for lv, rv in zip(lhs[0:2], rhs[0:2])] +
                [lv + rv for lv, rv in zip(lhs[2:4], rhs[2:4])])

    # Here we:
    # - Subtract the new means from the old data.
    # - Keep rhs's variance
    # This is used to use some file as "optimal truth" and to compute regret of
    # other files.
    elif op == '-m':
        return [lv - rv for lv, rv in zip(lhs[0:2], rhs[0:2])] + rhs[2:4]

    # Here we:
    # - Set the means equal to the old if they are lower than them.
    # - Do not touch variances
    # Here RHS is the previous timestep's data
    elif op == 'gt0':
        # Here we basically have to recompute all the cumulative data from
        # scratch since once we zero a negative all cumulative from there must
        # be changed.
        if lhs[0] >= 0.0:
            return [lhs[0], rhs[1] + lhs[0]] + lhs[2:4]
        return [0.0, rhs[1]] + lhs[2:4]

    else:
        return [] # Detect errors...

def secondPass(op, i, lhs, inputNum):
    # Here we:
    # - Average the summed means
    # - Average the summed variances
    if op == '+':
        data = [v / inputNum for v in lhs]

    # Here we:
    # - Average the summed variances
    elif op == '-':
        data = lhs[0:2] + [v / inputNum for v in lhs[2:4]]

    # Nothing to do
    else:
        data = lhs[:]

    data[2:4] = [math.sqrt(v) for v in data[2:4]]
    return data

# [[immediate mean, cumulative mean, immediate variance, cumulative variance]]
lhs = parseFile(files[0])
for f in files:
    if op in binaryops:
        if f == files[0]:
            continue
        rhs = parseFile(f, len(lhs))
    else:
        # Adjacent timesteps (if not, lhs only has enough information).
        # WARNING: Note that even though rhs is a copy separate from lhs, since
        # the elements inside are arrays, changing the contents of the arrays
        # inside lhs changes the ones in rhs as well! (This is useful though)
        rhs = [[0.0, 0.0, 0.0, 0.0]] + lhs[:-1]

    for i in range(len(lhs)):
        # Here we assign like this so that the original lhs array is not lost,
        # and this allows rhs (if needed) to reflect the changes of lhs
        lhs[i][:] = firstPass(op, i, lhs[i], rhs[i])

    print(lhs[-1])

for i in range(len(lhs)):
    # Postprocess data and back to stds
    lhs[i] = secondPass(op, i, lhs[i], len(files))
    # Make printable and put index back
    lhs[i] = " ".join([str(i)] + [str(v) for v in lhs[i]])
print(lhs[-1])

def mkdirMinusP(dirName):
    """ This function creates the folder specified, even if nested. """
    if dirName == "":
        return
    try:
        os.makedirs(dirName)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dirName):
            pass
        else:
            raise

mkdirMinusP(os.path.dirname(output))

# and write everything back
with open(output, 'w') as file:
    file.write("\n".join(lhs))
