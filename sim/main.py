#!/usr/bin/env python3
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
        wind_speed = mid#scipy.stats.norm.rvs(mid, diff, size=1)[0]

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

def main(y1, y2, y3, y4, y5, y6, y7):

    yaws = np.array([
        y1,
        y2,
        y3,
        y4,
        y5,
        y6,
        y7,
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
    
    return pp.tolist()

main(yaw_range1[0],
     yaw_range2[0],
     yaw_range1[0],
     yaw_range2[0],
     yaw_range1[0],
     yaw_range3[0],
     yaw_range1[0])
current = main(0, 0, 0, 0, 0, 0, 0)
best = main(27, -1, 27, -1, 27, 1, 27)
print(sum(current))
print(sum(best))
