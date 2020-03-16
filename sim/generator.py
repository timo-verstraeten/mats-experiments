#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Wrapper around FLORIS predictions.

@author: Timothy Verstraeten
@date: 28/11/2017
"""

import copy
import itertools
import json
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
import pickle
import time

import floris

class FlorisWrapper:
    """
    Call object.run(yaws) to simulate wake and retrieve the power production for each turbine.
    """

    def __init__(self, turbine_positions):
        # Read turbine and site specs
        with open('configs/specs_NREL_5MW.json', 'r') as f:
            self.turbine_specs = json.load(f)
        with open('configs/template_floris.json', 'r') as f:
            self.site = json.load(f)
        self.wind_speed = self.site["farm"]["properties"]["wind_speed"]
        
        # Add noise to the environmental conditions
        self.randomizeWind()

        # Adjust parameters
        for x, y in turbine_positions:
            self.site["farm"]["properties"]["layout_x"].append(x)
            self.site["farm"]["properties"]["layout_y"].append(y)
            self.site["turbines"].append(copy.deepcopy(self.turbine_specs))

    def randomizeWind(self):
        diff = 0.005
        mid = self.wind_speed - diff
        ub = mid + diff
        lb = mid - diff
        wind_speed = scipy.stats.norm.rvs(mid, diff, size=1)[0]

        wind_speed = min(wind_speed, ub)
        wind_speed = max(wind_speed, lb)

        self.site["farm"]["properties"]["wind_speed"] = wind_speed

    def run(self, yaws):
        # Set operational parameters
        for yaw, turbine in zip(yaws, self.site["turbines"]):
            turbine["properties"]["yaw_angle"] = yaw
        
        # Build simulator
        self.floris = floris.Floris(input_dict=self.site)
        
        # Compute power productions
        power_productions = [turbine.power for turbine in self.floris.farm.turbines]

        return np.array(power_productions)

    def plot_config(self, yaw_angles):
        X = self.site["farm"]["properties"]["layout_x"]
        Y = self.site["farm"]["properties"]["layout_y"]
        
        for x, y, yaw in zip(X, Y, yaw_angles):
            plt.plot([x, x + 500*np.cos(yaw*np.pi/180)], [y, y + 500*np.sin(yaw*np.pi/180)], 'r-')
            plt.plot(x, y, 'bo')
        plt.show()

use = 3

if (use == 0):
    # Grid structure
    #   (wind)>   0 1 2
    #   (wind)>   3 4 5
    h_distance = 2
    v_distance = 0.7
    turbine_grid = 500 * np.array([[0,  0],          [h_distance, 0],          [2*h_distance, 0],
                                   [0,  v_distance], [h_distance, v_distance], [2*h_distance, v_distance]])
    yaw_range1 = np.array([20, 29, 30, 35])
    yaw_range2 = np.array([30, 34, 37, 40])
    yaw_range3 = np.array([-5, -1, 0, 5])
elif (use == 1):
    # Grid structure
    #   (wind)>   0 1 2
    turbine_grid = 500 * np.array([[0,  0], [1, 0], [2, 0]])
    yaw_range1 = np.array([20, 29, 35])
    yaw_range2 = np.array([30, 34, 40])
    yaw_range3 = np.array([-5, 0, 5])
elif (use == 2):
    # Grid structure
    #   (wind)>   0 1 2 3
    #   (wind)>   4 5 6 7
    h_distance = 2.5
    v_distance = 1.0
    turbine_grid = 500 * np.array([[0,  0],          [h_distance, 0],          [2*h_distance, 0],          [3*h_distance, 0],
                                   [0,  v_distance], [h_distance, v_distance], [2*h_distance, v_distance], [3*h_distance, v_distance]])
    yaw_range1 = np.array([15, 20, 24])
    yaw_range2 = np.array([25, 30, 34])
    yaw_range3 = np.array([15, 20, 25])
    yaw_range4 = np.array([-5, 0, 5])
elif (use == 3):
    # Grid structure
    #   (wind)>     0 7
    #   (wind)>   1
    #   (wind)>     2 8
    #   (wind)>   3
    #   (wind)>     4 9
    #   (wind)>   5
    #   (wind)>     6 10
    h_distance = 2
    v_distance = 0.75
    turbine_grid = 500 * np.array([[h_distance,  0],
                                   [0, 2*v_distance],
                                   [h_distance, 3*v_distance],
                                   [0, 5*v_distance],
                                   [h_distance, 6*v_distance],
                                   [0, 7*v_distance],
                                   [h_distance, 9*v_distance],
                                   [1+h_distance, 0],
                                   [1+h_distance, 3*v_distance],
                                   [1+h_distance, 6*v_distance],
                                   [1+h_distance, 9*v_distance]])
    yaw_range1 = np.array([23, 27, 28])
    yaw_range2 = np.array([-10, -6, -1])
    yaw_range3 = np.array([-2, 1, 4])
    yaw_range4 = np.array([0])


simulator = FlorisWrapper(turbine_grid)

#def main(y1, y2, y3, y4, y5, y6, y7, y8):
def main(y1, y2, y3, y4, y5, y6, y7):
#def main(y1, y2, y3):

    yaws = np.array([
        yaw_range1[y1],
        yaw_range2[y2],
        yaw_range1[y3],
        yaw_range2[y4],
        yaw_range1[y5],
        yaw_range3[y6],
        yaw_range1[y7],
        0,
        0,
        0,
        0
    ])

    #best_yaws          = np.array([27, -1, 27, -1, 27,  1, 27,  0,  0,  0,  0])
    #lowest_single_yaws = np.array([ 23, -10,  23, -10,  23,  -2,  23,   0,   0,   0,   0])

    simulator.randomizeWind()
    q = simulator.run(yaws)
    #max_v = sum(simulator.run(best_yaws))
    #min_single_v = min(simulator.run(lowest_single_yaws))

    pp = np.copy(q[0:7])
    pp[0] += q[7]
    pp[2] += q[8]
    pp[4] += q[9]
    pp[6] += q[10]
    #print("######")
    #print([y1, y2, y3, y4, y5, y6])
    #print(yaws)
    #print(pp.tolist() + [max_v, min_single_v])
    #print("######")
    return pp.tolist() #+ [max_v, min_single_v]

def test():
    print("Running test...")
    best_power, best_yaws = float("-inf"), None
    min_power, min_single_power = float("+inf"), float("+inf")
    min_p_y = None # best_yaws = np.array([27, -1, 27, -1, 27,  1, 27,  0,  0,  0,  0])
    start = time.time()
    #best_yaws          = np.array([27, -1, 27, -1, 27,  1, 27,  0,  0,  0,  0])
    #lowest_single_yaws = np.array([ 23, -10,  23, -10,  23,  -2,  23,   0,   0,   0,   0])
    #print min(simulator.run(lowest_single_yaws))
    #return
    for yyaws in itertools.product(yaw_range1, yaw_range2,
                                   yaw_range1, yaw_range2,
                                   yaw_range1, yaw_range3,
                                   yaw_range1,
                                   yaw_range4, yaw_range4, yaw_range4, yaw_range4):
        yaws = np.array(list(yyaws))
        powers = simulator.run(yaws)
        pp = np.copy(powers[0:7])
        pp[0] += powers[7]
        pp[2] += powers[8]
        pp[4] += powers[9]
        pp[6] += powers[10]
        power = sum(powers)
        if power > best_power:
            best_power, best_yaws = power, yaws
        if power < min_power:
            min_power = power
        minpp = min(pp)
        if minpp < min_single_power:
            min_single_power, min_p_y = minpp, yaws

    print(time.time() - start)
    print(best_power, min_power, min_single_power, best_yaws, min_p_y)
    simulator.plot_config(best_yaws)

if __name__ == "__main__":
    test()
