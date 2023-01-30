#!/usr/bin/env python
from math import sqrt
import os
import sys
import random
import matplotlib.pyplot as plt
import numpy as np

from utils import check_sumo_env

check_sumo_env()
import traci
from traci import StepListener, constants as tc
from plexe import (
    Plexe,
    ACC,
    CACC,
    GEAR,
    RPM,
    CONSENSUS,
    PLOEG,
    ENGINE_MODEL_REALISTIC,
    FAKED_CACC,
)
from utils import (
    start_sumo,
    running,
    add_platooning_vehicle,
    add_vehicle,
    communicate,
    get_distance,
)

START_STEP = 66

# vehicle length
LENGTH = 8
# inter-vehicle distance

# cruising speed
SPEED = 27
# lane_number latoon insert
LANE_NUM = 2
LEADER = "p.0"
N_VEHICLES = 6
CHECK_ALL = 0b01111  # SpeedMode

VTYPE_LIST = [
    "truck0",
    "truck1",
    "truck2",
    "car0",
    "car1",
    "car2",
]

def get_length(type_index):
    if type_index > 0:
        i = type_index
    else:
        i = type_index+1
    return float(traci.vehicletype.getLength(VTYPE_LIST[i]))


def cacc_spacing(type_index):
    if type_index > 0:
        space = get_length(type_index)
    else:
        space = get_length(type_index+1)
    return sqrt(space)*1.5
    
def get_position(init_position):
    current = init_position
    def f(length):
        nonlocal current
        current -= length
        return current
    return f

def add_vehicles(plexe, n, position, real_engine=False):
    topology = {}
    get_insert_postion = get_position(position)
    for i in range(n):
        vid = "p.%d" % i
        insert_postion = get_insert_postion(cacc_spacing(i-1)+get_length(i-1))
        # print(insert_postion)
        add_platooning_vehicle(
            plexe,
            vid,
            insert_postion,
            LANE_NUM,
            SPEED,
            cacc_spacing(i-1)-1,
            real_engine,
            VTYPE_LIST[i],
        )
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.set_cc_desired_speed(vid, 33)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
        else:
            plexe.set_active_controller(vid, CACC)
            # plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i - 1))
            plexe.add_member(LEADER, vid, i)
        if i > 0:
            topology[vid] = {"front": "p.%d" % (i - 1), "leader": LEADER}
        plexe.set_fixed_lane(vid, LANE_NUM, safe=False)
    return topology


def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    random.seed(1)
    start_sumo("../cfg/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    topology = {}
    x = []
    while running(demo_mode, step, 6000):
        traci.simulationStep()
        # when reaching 60 seconds, reset the simulation when in demo_mode
        if demo_mode and step == 600000:
            start_sumo("../cfg/freeway.sumo.cfg", True)
            step = 1
            random.seed(1)

        if step > START_STEP and step % 10 == 1:
            communicate(plexe, topology)
            # distanceP = get_distance(plexe, "p.0", "p.1")
            # print(distanceP)

            pass
        
        if  step > START_STEP + 16000 and step % 100 == 1:
            distance_list = [0.0]*5
            for i in range(0,N_VEHICLES-1):
                distance_list[i] = get_distance(plexe, "p.%d"%i, "p.%d"%(i+1))
                pass

            x.append(distance_list)
            print(distance_list)

            pass

        if step == 30000 :
            x_index = len(x)
            data = np.asmatrix(x)
            
            data = data.T
            for i in range(5):
                plt.plot(range(x_index),data[i].T,'s-',color = 'r',label="ATT-RLSTM")
            plt.show()



            # print(x)
        if step < 100 and step % 3 == 0:
            pass
        else:
            pass

        if step == START_STEP:
            topology = add_vehicles(plexe, N_VEHICLES, 180, real_engine)
            plexe.enable_auto_lane_changing(LEADER, True)
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 2000)
        step += 1

    traci.close()


if __name__ == "__main__":
    main(True, False)
