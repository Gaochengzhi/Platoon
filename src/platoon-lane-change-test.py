#!/usr/bin/env python

import os
import sys
import random

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from traci import constants as tc
from plexe import Plexe, ACC, CACC, GEAR, RPM
from utils import start_sumo, running, add_platooning_vehicle, add_vehicle


# vehicle length
LENGTH = 9
# inter-vehicle distance
DISTANCE = 4
# cruising speed
SPEED = 55

LEADER = "p.0"
N_VEHICLES = 5


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
    for i in range(n):
        vid = "p.%d" % i
        add_platooning_vehicle(plexe, vid, position - i * (DISTANCE + LENGTH),
                               0, SPEED, DISTANCE, real_engine)
        plexe.set_fixed_lane(vid, 0, safe=False)
        traci.vehicle.setSpeedMode(vid, 0)
        traci.vehicle.setLength(vid,5)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            plexe.enable_auto_lane_changing(LEADER, True)
        else:
            plexe.set_active_controller(vid, CACC)
            plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i-1))
            plexe.add_member(LEADER, vid, i)


def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    random.seed(1)
    start_sumo("../cfg/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    while running(demo_mode, step, 6000):

        # when reaching 60 seconds, reset the simulation when in demo_mode
        if demo_mode and step == 6000:
            start_sumo("../cfg/freeway.sumo.cfg", True)
            step = 0
            random.seed(1)

        traci.simulationStep()

        if step == 1:
            add_vehicles(plexe, N_VEHICLES, 150, real_engine)
            add_vehicle(plexe, "v0", 140, 1, 25, "passenger")
            add_vehicle(plexe, "v1", 340, 0, 20, "passenger2")
            add_vehicle(plexe, "v2", 400, 0, 20, "passenger2")
            add_vehicle(plexe, "v3", 450, 1, 25, "passenger2")
            add_vehicle(plexe, "v4", 400, 1, 25, "passenger2")
            add_vehicle(plexe, "v5", 500, 1, 25, "passenger2")
            add_vehicle(plexe, "v6", 450, 0, 25, "passenger2")
            add_vehicle(plexe, "v7", 400, 0, 25, "passenger2")
            add_vehicle(plexe, "v8", 500, 0, 25, "passenger2")
            add_vehicle(plexe, "v9", 450, 2, 25, "passenger2")
            add_vehicle(plexe, "v10", 400, 3, 25, "passenger2")
            add_vehicle(plexe, "v11", 500, 3, 25, "passenger2")
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 30000)
            print("\n\n\nThis is my try to debug\n\n\n")




        if real_engine and setter is not None:
            # if we are running with the dashboard, update its values
            tracked_id = traci.gui.getTrackedVehicle("View #0")
            if tracked_id != "":
                ed = plexe.get_engine_data(tracked_id)
                vd = plexe.get_vehicle_data(tracked_id)
                setter(ed[RPM], ed[GEAR], vd.speed, vd.acceleration)

        if step >= 4:
            if plexe.get_crashed("p.3"):
                print("\n CRASHED!",plexe.get_crashed("p.3"))
            if step%10 == 0:
                print("p3 speed,distance of p1~p2:",
                traci.vehicle.getSpeed("p.3"),
                plexe.get_distance_from_begin("p.1") - plexe.get_distance_from_begin("p.2")
                      
                      )
        step += 1

    traci.close()


if __name__ == "__main__":
    main(True, False)
