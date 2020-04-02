#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Wrapper around FLORIS predictions.

@author: Timothy Verstraeten
@date: 28/11/2017
"""

import itertools
import matplotlib.pyplot as plt
import numpy as np
import pickle
import time

from Parameters import FLORISParameters
from Circle_assembly import floris_assembly_opt_AEP


class FlorisWrapper:
    """
    Call object.run(yaws) to simulate wake and retrieve the power production for each turbine.
    """

    def __init__(self, turbine_positions, wind_angle=0., wind_speed=8.1):
        n_turbines = turbine_positions.shape[0]
        nrel_prop = pickle.load(open('NREL5MWCPCT.p'))
        floris = floris_assembly_opt_AEP(nTurbines=n_turbines, nDirections=1, datasize=nrel_prop.CP.size)
        floris.parameters = FLORISParameters()  # use default FLORIS parameters

        # Define site measurements
        floris.windrose_directions = wind_angle * np.ones(1)  # incoming wind direction (deg)
        floris.windrose_speeds = wind_speed  # incoming wind speed (m/s)
        floris.air_density = 1.1716
        floris.initVelocitiesTurbines = np.ones_like(floris.windrose_directions)*floris.windrose_speeds

        # Define turbine properties
        floris.curve_wind_speed = nrel_prop.wind_speed
        floris.curve_CP = nrel_prop.CP
        floris.curve_CT = nrel_prop.CT
        floris.axialInduction = 1.0/3.0 * np.ones(n_turbines)  # used only for initialization
        floris.rotorDiameter = 126.4 * np.ones(n_turbines)
        floris.rotorArea = np.pi * floris.rotorDiameter[0]**2 / 4.0 * np.ones(n_turbines)
        floris.hubHeight = 90.0 * np.ones(n_turbines)
        floris.generator_efficiency = 0.944 * np.ones(n_turbines)
        floris.turbineX, floris.turbineY = np.array(list(zip(*turbine_positions)))

        self.floris = floris

    def run(self, yaws):
        self.floris.yaw = yaws
        self.floris.run()
        return np.array(self.floris.floris_power_0.wt_power)

    def plot_config(self):
        for x, y, yaw in zip(self.floris.turbineX, self.floris.turbineY, self.floris.yaws):
            plt.plot([x, x + 500*np.cos(yaw*np.pi/180)], [y, y + 500*np.sin(yaw*np.pi/180)], 'r-')
            plt.plot(x, y, 'bo')
        plt.show()

def test_one():
    # One turbine
    #    FARM:
    #        (wind)>   0 1
    turbine_grid = 500 * np.array([[0,  0]])
    simulator = FlorisWrapper(turbine_grid)
    yaw_range = np.array([-2, -1, 0, 1, 2])
    best_power, best_yaws = float("-inf"), None
    start = time.time()
    for yaw in yaw_range:
        yaws = np.array([yaw])
        power = sum(simulator.run(yaws))
        if power > best_power:
            best_power, best_yaws = power, yaws
    print(time.time() - start)  # about 0.2 seconds
    print(best_power, best_yaws)  # (1708.0171030711763, array([0]))

def test_two():
    # Two turbines
    #    FARM:
    #        (wind)>   0 1
    turbine_grid = 500 * np.array([[0,  0], [1, 0], [2, 0]])
    simulator = FlorisWrapper(turbine_grid)
    yaw_range = np.array([28, 29, 33, 34, 35])
    yaw_range2 = np.array([-1, 0, 1])
    best_power, best_yaws = float("-inf"), None
    min_single_power = float("+inf")
    start = time.time()
    for yaws in itertools.product(yaw_range, yaw_range, yaw_range2):
        yaws = np.array(list(yaws))
        powers = simulator.run(yaws)
        power = sum(powers)
        if power > best_power:
            best_power, best_yaws = power, yaws
        if min(powers) < min_single_power:
            min_single_power = min(powers)
    print(time.time() - start)  # about 0.5 seconds
    print(best_power, min_single_power, best_yaws)  # (2344.9663252982664, array([10,  0]))


def test_grid():
    # Grid structure
    #    FARM:
    #        (wind)>   0 1 2
    #        (wind)>   3 4 5
    turbine_grid = 500 * np.array([[0,  0], [1, 0], [2, 0],
                                   [0,  3], [1, 3], [2, 3]])
    simulator = FlorisWrapper(turbine_grid)
    yaw_range = np.array([-10, -5, 0, 5, 10])
    best_power, best_yaws = float("-inf"), None
    min_single_power = float("+inf")
    start = time.time()
    for yyaws in itertools.product(yaw_range, yaw_range, yaw_range, yaw_range, yaw_range, yaw_range):
        yaws = np.array(list(yyaws))
        powers = simulator.run(yaws)
        power = sum(powers)
        if power > best_power:
            best_power, best_yaws = power, yaws
        if min(powers) < min_single_power:
            min_single_power = min(powers)
    print(time.time() - start)  # about 100 seconds
    print(best_power, best_yaws)  # (5624.0506443859558, array([10, 10,  0, 10, 10,  0]))

def test_grid2():
    # Grid structure
    #    FARM:
    #        (wind)>   0 1 2
    #        (wind)>   3 4 5
    h_distance = 2.5
    v_distance = 0.5
    turbine_grid = 500 * np.array([[0,  0],          [h_distance, 0],          [2*h_distance, 0],          [3*h_distance, 0],
                                   [0,  v_distance], [h_distance, v_distance], [2*h_distance, v_distance], [3*h_distance, v_distance]])
    yaw_range1 = np.array([15, 20, 24])
    yaw_range2 = np.array([25, 30, 34])
    yaw_range3 = np.array([15, 20, 25])
    yaw_range4 = np.array([-5, 0, 5])

    simulator = FlorisWrapper(turbine_grid)
    best_power, best_yaws = float("-inf"), None
    min_single_power = float("+inf")
    start = time.time()
    for yyaws in itertools.product(yaw_range1, yaw_range2, yaw_range3, yaw_range4,
                                   yaw_range1, yaw_range2, yaw_range3, yaw_range4):
        yaws = np.array(list(yyaws))
        powers = simulator.run(yaws)
        power = sum(powers)
        if power > best_power:
            best_power, best_yaws = power, yaws
        if min(powers) < min_single_power:
            min_single_power = min(powers)
    print(time.time() - start)  # about 100 seconds
    print(best_power, min_single_power, best_yaws)  # (5624.0506443859558, array([10, 10,  0, 10, 10,  0]))

def test_shifted_grid():
    # Shifted grid structure
    #    FARM:
    #        (wind)>   0   1
    #        (wind)>     2   3
    #        (wind)>   4   5
    turbine_grid = 300 * np.array([[0, 0], [1, 0],
                                   [0.5, 0.5], [1.5, 0.5],
                                   [0, 1], [1, 1]])
    simulator = FlorisWrapper(turbine_grid, wind_speed=10)
    yaw_range = np.array([-10, -5, 0, 5, 10])
    best_power, best_yaws = float("-inf"), None
    start = time.time()
    for yaw1, yaw2, yaw3, yaw4, yaw5, yaw6 in itertools.product(yaw_range, yaw_range, yaw_range, yaw_range, yaw_range, yaw_range):
        yaws = np.array([yaw1, yaw2, yaw3, yaw4, yaw5, yaw6])
        power = sum(simulator.run(yaws))
        if power > best_power:
            best_power, best_yaws = power, yaws
    print(time.time() - start)  # about 100 seconds
    print(best_power, best_yaws)  # (5624.0506443859558, array([10, 10,  0, 10, 10,  0]))

def test_complex():
    # Shifted grid structure
    #    FARM:
    #        (wind)>   0   1
    #        (wind)>     2   3
    #        (wind)>   4   5
    turbine_grid = np.array([[0, 0], [500, 0],
                             [300, 500], [800, 500],
                             [600, 1000], [1100, 1000]])
    turbine_grid = np.array([[0, 0], [500, 0],
                             [300, 500], [800, 500],
                             [600, 1000], [1100, 1000]])
    simulator = FlorisWrapper(turbine_grid, wind_speed=10, wind_angle=20)
    yaw_range = np.array([-10, -5, 0, 5, 10])+20
    best_power, best_yaws = float("-inf"), None
    start = time.time()
    for yaw1, yaw2, yaw3, yaw4, yaw5, yaw6 in itertools.product(yaw_range, yaw_range, yaw_range, yaw_range, yaw_range, yaw_range):
        yaws = np.array([yaw1, yaw2, yaw3, yaw4, yaw5, yaw6])
        power = sum(simulator.run(yaws))
        if power > best_power:
            best_power, best_yaws = power, yaws
    print(time.time() - start)  # about 100 seconds
    print(best_power, best_yaws)  # (5624.0506443859558, array([10, 10,  0, 10, 10,  0]))

test_grid2()
