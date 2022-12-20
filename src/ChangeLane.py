#!/usr/bin/env python

import os
import sys
import random

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci

from traci import StepListener, constants as tc
from plexe import Plexe, ACC, CACC, GEAR, RPM, CONSENSUS, PLOEG, ENGINE_MODEL_REALISTIC,FAKED_CACC
from utils import start_sumo, running, add_platooning_vehicle, add_vehicle, communicate,get_distance


# vehicle length
LENGTH = 10
# inter-vehicle distance
DISTANCE = 9
# cruising speed
SPEED = 20

LANE_NUM = 4

# VEHICLES = ["alfa-147", "audi-r8", "bugatti-veyron"]
LEADER = "p.0"
N_VEHICLES = 6
JOIN_DISTANCE = DISTANCE * 2
GOING_TO_POSITION = 0
OPENING_GAP = 1
COMPLETED = 2
CHECK_ALL = 0b01111  # SpeedMode

VTYPE_LIST = [
    "truck0",
    "truck1",
    "truck2",
    "car0",
    "car1",
    "car2",
]
JOIN_DISTANCE = DISTANCE * 2


# maneuver actors
JOIN_POSITION = 3
FRONT_JOIN = "p.%d" % (JOIN_POSITION - 1)
BEHIND_JOIN = "p.%d" % JOIN_POSITION
JOINER = "p.%d" % N_VEHICLES


def add_vehicles(plexe, n, position, real_engine=False):
    # add a platoon of n vehicles
    topology = {}
    for i in range(n):
        vid = "p.%d" % i
        vtype_length = float(traci.vehicletype.getLength(VTYPE_LIST[i]))
        vtyep_minGap = float(traci.vehicletype.getMinGap(VTYPE_LIST[i]))
        print(vtype_length)
        print(vtyep_minGap)
        add_platooning_vehicle(
            plexe,
            vid,
            position - i * (LENGTH+DISTANCE),
            LANE_NUM,
            SPEED,
            vtyep_minGap,
            real_engine,
            VTYPE_LIST[i]
        )
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.set_cc_desired_speed(vid, 25)
        if i == 0:
            plexe.set_active_controller(vid,ACC)
        else:
            plexe.set_active_controller(vid,CACC)
            plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i - 1))
            plexe.add_member(LEADER, vid, i)
        if i > 0:
            topology[vid] = {"front": "p.%d" % (i - 1), "leader": LEADER}
        plexe.set_fixed_lane(vid, LANE_NUM, safe=False)
    return topology



def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    random.seed(1)
    record_time = 0
    start_sumo("../cfg/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    topology = {}
    while running(demo_mode, step, 6000):
        state = GOING_TO_POSITION
        traci.simulationStep()
        # when reaching 60 seconds, reset the simulation when in demo_mode
        if demo_mode and step == 6000:
            start_sumo("../cfg/freeway.sumo.cfg", True)
            step = 1
            random.seed(1)

        if step > 110 and step % 10 == 1:
            # simulate vehicle communication every 100 ms
            communicate(plexe, topology)
        if step < 100 and step % 3 == 0:
            # add_vehicle(plexe, "v%d.%d" % (step,0), 14, 0, 15, "passenger")
            # add_vehicle(plexe, "v0", 140, 1, 25, "vtypeauto")
            # add_vehicle(plexe, "v%d.%d" % (step,1), 14, 1, 5, "vtypeauto")
            # add_vehicle(plexe, "v%d.%d" % (step,0), 14, 0, 15, "passenger")
            # add_vehicle(plexe, "v%d.%d" % (step,4), 14, 2, 5, "vtypeauto")
            pass
        else:
            pass


        if step == 110:
            topology = add_vehicles(plexe, N_VEHICLES, 180, real_engine)
            plexe.enable_auto_lane_changing(LEADER,True)
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 2000)
            print("\n\n\nThis is my try to debug\n\n\n")


                # plexe.enable_auto_lane_changing(LEADER, True)

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
