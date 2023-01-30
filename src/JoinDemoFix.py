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



# maneuver actors
JOIN_POSITION = 3
FRONT_JOIN = "p.%d" % (JOIN_POSITION - 1)
BEHIND_JOIN = "p.%d" % JOIN_POSITION
JOINER = "p.%d" % N_VEHICLES

def getVlength(vtypeIndex):
    return float(traci.vehicletype.getLength(VTYPE_LIST[vtypeIndex]))

def getDistance(vtypeIndex):
    return float(traci.vehicletype.getMinGap(VTYPE_LIST[vtypeIndex]))+3

def add_vehicles(plexe, n, position, real_engine=False):
    # add a platoon of n vehicles
    topology = {}
    for i in range(n):
        vid = "p.%d" % i
        vtype_length = getVlength(i)
        vtyep_minGap = getDistance(i)
        print("my:",vtyep_minGap+vtype_length)
        print("correct",DISTANCE+LENGTH)
        add_platooning_vehicle(
            plexe,
            vid,
            position - i * (DISTANCE+LENGTH),
            LANE_NUM,
            SPEED,
            vtyep_minGap,
            real_engine,
            VTYPE_LIST[i]
        )
        plexe.set_fixed_lane(vid, LANE_NUM, safe=False)
        traci.vehicle.setSpeedMode(vid, 0)
        
        plexe.set_cc_desired_speed(vid, 25)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            traci.vehicle.setSpeedMode(vid, 0)
        else:
            plexe.set_active_controller(vid,CACC)
            plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i - 1))
            plexe.add_member(LEADER, vid, i)
        if i > 0:
            topology[vid] = {"front": "p.%d" % (i - 1), "leader": LEADER}
    vid = "p.%d" % n
    add_platooning_vehicle(plexe, vid, 10, 2, SPEED, getDistance(n-1), real_engine,VTYPE_LIST[n-1])
    # plexe.set_fixed_lane(vid, LANE_NUM-1, safe=False)
    plexe.set_active_controller(vid, CACC)
    plexe.set_path_cacc_parameters(vid, distance=JOIN_DISTANCE)
    plexe.enable_auto_lane_changing(vid,False)
    return topology

def get_in_position(plexe, jid, fid, topology):
    """
    Makes the joining vehicle get close to the join position. This is done by
    changing the topology and setting the leader and the front vehicle for
    the joiner. In addition, we increase the cruising speed and we switch to
    the "fake" CACC, which uses a given GPS distance instead of the radar
    distance to compute the control action
    :param plexe: API instance
    :param jid: id of the joiner
    :param fid: id of the vehicle that will become the predecessor of the joiner
    :param topology: the current platoon topology
    :return: the modified topology
    """
    topology[jid] = {"leader": LEADER, "front": fid}
    plexe.set_cc_desired_speed(jid, SPEED + 15)
    plexe.set_active_controller(jid, FAKED_CACC)
    return topology

def open_gap(plexe, vid, jid, topology, n):
    """
    Makes the vehicle that will be behind the joiner open a gap to let the
    joiner in. This is done by creating a temporary platoon, i.e., setting
    the leader of all vehicles behind to the one that opens the gap and then
    setting the front vehicle of the latter to be the joiner. To properly
    open the gap, the vehicle leaving space switches to the "fake" CACC,
    to consider the GPS distance to the joiner
    :param plexe: API instance
    :param vid: vehicle that should open the gap
    :param jid: id of the joiner
    :param topology: the current platoon topology
    :param n: total number of vehicles currently in the platoon
    :return: the modified topology
    """
    index = int(vid.split(".")[1])
    for i in range(index + 1, n):
        # temporarily change the leader
        topology["p.%d" % i]["leader"] = vid
    # the front vehicle if the vehicle opening the gap is the joiner
    topology[vid]["front"] = jid
    plexe.set_active_controller(vid, FAKED_CACC)
    plexe.set_path_cacc_parameters(vid, distance=40)
    return topology


def reset_leader(vid, topology, n):
    """
    After the maneuver is completed, the vehicles behind the one that opened
    the gap, reset the leader to the initial one
    :param vid: id of the vehicle that let the joiner in
    :param topology: the current platoon topology
    :param n: total number of vehicles in the platoon (before the joiner)
    :return: the modified topology
    """
    index = int(vid.split(".")[1])
    for i in range(index + 1, n):
        # restore the real leader
        topology["p.%d" % i]["leader"] = LEADER
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

        if step > 11 and step % 10 == 1:
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


        if step == 11:
            topology = add_vehicles(plexe, N_VEHICLES, 180, real_engine)
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 2000)
            print("\n\n\nThis is my try to debug\n\n\n")
        if step == 21:
            topology = get_in_position(plexe, JOINER, FRONT_JOIN, topology)
            if traci.vehicle.getLaneIndex(JOINER) == 0:
                record_time += 1
                if record_time == 30:
                    plexe.enable_auto_lane_changing(LEADER,True)
                    print("changelane")
                pass

        if state == GOING_TO_POSITION and step > 11:
            # when the distance of the joiner is small enough, let the others
            # open a gap to let the joiner enter the platoon
            if get_distance(plexe, JOINER, FRONT_JOIN) < JOIN_DISTANCE + 1:
                state = OPENING_GAP
                topology = open_gap(plexe, BEHIND_JOIN, JOINER, topology,
                                    N_VEHICLES)
        if state == OPENING_GAP:
            # when the gap is large enough, complete the maneuver
            if get_distance(plexe, BEHIND_JOIN, FRONT_JOIN) > \
                    2 * JOIN_DISTANCE + 2:
                state = COMPLETED
                print("sadkh")
                # traci.vehicle.changeLane("p.6",lane,12)
                
                lane = traci.vehicle.getLaneIndex(LEADER)
                plexe.set_fixed_lane(JOINER, lane, safe=False)
                # plexe.enable_auto_lane_changing(LEADER, True)
                plexe.set_active_controller(JOINER, CACC)
                traci.vehicle.setSpeed(JOINER,"22.8")
                plexe.set_path_cacc_parameters(JOINER, distance=DISTANCE)
                plexe.set_active_controller(BEHIND_JOIN, CACC)
                plexe.set_path_cacc_parameters(BEHIND_JOIN, distance=DISTANCE)
                topology = reset_leader(BEHIND_JOIN, topology, N_VEHICLES)

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
