#!/usr/bin/env python

import os
from pickle import FALSE, TRUE
import sys
import random

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci

from traci import StepListener, constants as tc
from plexe import Plexe, ACC, CACC, GEAR, RPM ,CONSENSUS,PLOEG, ENGINE_MODEL_REALISTIC
from utils import start_sumo, running, add_platooning_vehicle, add_vehicle, communicate


# vehicle length
LENGTH = 4
# inter-vehicle distance
DISTANCE = 5
# cruising speed
SPEED = 2

VEHICLES = ["alfa-147", "audi-r8", "bugatti-veyron"]
LEADER = "p.0"
N_VEHICLES = 4
JOIN_DISTANCE = DISTANCE * 2
GOING_TO_POSITION = 0
OPENING_GAP = 1
COMPLETED = 2
CHECK_ALL = 0B01111 # SpeedMode


def add_vehicles(plexe, n, position, real_engine=False):
    """
    Adds a platoon of n vehicles to the simulation, plus an additional one
    farther away that wants to join the platoon
    :param plexe: API instance
    :param n: number of vehicles of the platoon
    :param position: position of the leader
    :param real_engine: set to true to use the realistic engine model,
    false to use a first order lag model
    """
    # add a platoon of n vehicles
    topology = {}
    for i in range(n):
        vid = "p.%d" % i
        add_platooning_vehicle(plexe, vid, position - i * (DISTANCE + LENGTH),
                               3, SPEED, DISTANCE, real_engine)
        # plexe.set_fixed_lane(vid, 3, safe=False)
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.set_cc_desired_speed(vid, 10)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            plexe.enable_auto_lane_changing(LEADER, True)
        else:
            plexe.set_active_controller(vid, CACC)
            plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i-1))
            plexe.add_member(LEADER, vid, i)
        if i >= 0:
            topology[vid] = {"front": "p.%d" % (i - 1), "leader": LEADER}

    return topology


def add_vehicles2(plexe, n, position, real_engine=True):
    """
    Adds a platoon of n vehicles to the simulation, plus an additional one
    farther away that wants to join the platoon
    :param plexe: API instance
    :param n: number of vehicles of the platoon
    :param position: position of the leader
    :param real_engine: set to true to use the realistic engine model,
    false to use a first order lag model
    """
    # add a platoon of n vehicles
    topology = {}
    for i in range(n):
        vid = "p.%d"%i
        # plexe.set_fixed_lane(vid, 0, False)
        # plexe.set_engine_model(vid, ENGINE_MODEL_REALISTIC)
        # plexe.set_vehicles_file(vid, "vehicles.xml")
        # plexe.set_vehicle_model(vid,vid)
        if i == 0:
            plexe.set_active_controller(vid,ACC)
            plexe.enable_auto_lane_changing(LEADER,TRUE)
        else:
            plexe.set_active_controller(vid,CACC)
            plexe.enable_auto_feed(vid,TRUE, LEADER, "p.%d" % (i-1))
            plexe.add_member(LEADER, vid, i*2)
            plexe.set_acc_headway_time(vid,2)
        if i >= 0:
            topology[vid] = {"front": "v.%d" % (i - 1), "leader": LEADER}
        traci.vehicle.setSpeedMode(vid, CHECK_ALL)
        plexe.use_prediction(vid,TRUE)
        add_platooning_vehicle(plexe,vid, position - i * (DISTANCE + LENGTH),
                               3, SPEED, DISTANCE, real_engine)

    return topology


def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    random.seed(1)
    start_sumo("../cfg/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    topology ={}
    while running(demo_mode, step, 6000):

        traci.simulationStep()
        # when reaching 60 seconds, reset the simulation when in demo_mode
        if demo_mode and step == 6000:
            start_sumo("../cfg/freeway.sumo.cfg", True)
            step = 1
            random.seed(1)

        if step> 11 and step % 10 == 1:
            # simulate vehicle communication every 100 ms
            # communicate(plexe, topology) 
            # print(topology)
            pass
            

        if step < 100 and step%3 == 0:
            # add_vehicle(plexe, "v%d.%d" % (step,0), 14, 0, 15, "passenger")
            # add_vehicle(plexe, "v0", 140, 1, 25, "vtypeauto")
            # add_vehicle(plexe, "v%d.%d" % (step,1), 14, 1, 5, "vtypeauto")
            # add_vehicle(plexe, "v%d.%d" % (step,0), 14, 0, 15, "passenger")
            # add_vehicle(plexe, "v%d.%d" % (step,4), 14, 2, 5, "vtypeauto")
            pass
        else:
            pass
            

        if step == 101:
            topology = add_vehicles(plexe, N_VEHICLES, 80, real_engine)
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 2000)
            print("\n\n\nThis is my try to debug\n\n\n")
        




        # if real_engine and setter is not None:
        #     # if we are running with the dashboard, update its values
        #     tracked_id = traci.gui.getTrackedVehicle("View #0")
        #     if tracked_id != "":
        #         ed = plexe.get_engine_data(tracked_id)
        #         vd = plexe.get_vehicle_data(tracked_id)
        #         setter(ed[RPM], ed[GEAR], vd.speed, vd.acceleration)
        #
        # if step >= 001:
        #     if plexe.get_crashed("p.0"):
        #         print("\n CRASHED!",plexe.get_crashed("p.0"))
        #     if step%10 == 0:
        #         print("p0 speed,distance of p1~p2:",
        #         traci.vehicle.getSpeed("p.0"),
        #         plexe.get_distance_from_begin("p.1") - plexe.get_distance_from_begin("p.2"))

        step += 1

    traci.close()


if __name__ == "__main__":
    main(True, False)
