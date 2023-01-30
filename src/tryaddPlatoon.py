#!/usr/bin/env python
from math import sqrt
import os
import sys
import random

from utils import check_sumo_env, sumolib
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
    plexe,
)
from utils import (
    start_sumo,
    running,
    add_platooning_vehicle,
    add_vehicle,
    communicate,
    get_distance,
    get_status
)

START_STEP = 36

# vehicle length
LENGTH = 8
# inter-vehicle distance
JOIN_DISTANCE = 8
# cruising speed
SPEED = 33
# lane_number platoon insert
LANE_NUM = 2
LEADER = "p.0"
N_VEHICLES = 6
CHECK_ALL = 0b01111  # SpeedMode


# maneuver actors
JOIN_POSITION = 4
FRONT_JOIN = "p.%d" % (JOIN_POSITION - 1)
BEHIND_JOIN = "p.%d" % JOIN_POSITION
JOINER = "p.%d" % N_VEHICLES

# maneuver states:
GOING_TO_POSITION = 0
OPENING_GAP = 1
COMPLETED = 2
DISTANCE = 4

DELAY_TIME = 0

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
        i = type_index + 1
    return float(traci.vehicletype.getLength(VTYPE_LIST[i]))


def cacc_spacing(type_index):
    if type_index > 0:
        space = get_length(type_index)
    else:
        space = get_length(type_index + 1)
    return sqrt(space) * 1.8


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
        insert_postion = get_insert_postion(cacc_spacing(i - 1) + get_length(i - 1))
        # print(insert_postion)
        add_platooning_vehicle(
            plexe,
            vid,
            insert_postion,
            LANE_NUM,
            SPEED,
            cacc_spacing(i - 1),
            real_engine,
            VTYPE_LIST[i],
        )
        traci.vehicle.setSpeedMode(vid, CHECK_ALL)
        plexe.set_cc_desired_speed(vid, SPEED)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
        else:
            plexe.set_active_controller(vid, CACC)
            # plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i - 1))
            plexe.add_member(LEADER, vid, i)
        if i > 0:
            plexe.use_controller_acceleration(vid, False)
            topology[vid] = {"front": "p.%d" % (i - 1), "leader": LEADER}
        plexe.set_fixed_lane(vid, LANE_NUM, safe=False)
        traci.vehicle.setSpeedMode(LEADER,CHECK_ALL)
    vid = "p.%d" % n
    add_platooning_vehicle(
        plexe, vid, 1, 1, 33, cacc_spacing(n - 1), real_engine, VTYPE_LIST[n - 1]
    )
    plexe.set_fixed_lane(vid, 1, safe=False)
    plexe.set_active_controller(vid, ACC)
    plexe.use_controller_acceleration(vid, False)
    plexe.set_path_cacc_parameters(vid, distance=cacc_spacing(n - 1))
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
    plexe.set_cc_desired_speed(jid, SPEED + 10)
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
    plexe.set_path_cacc_parameters(vid, distance=JOIN_DISTANCE)
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
    start_sumo("../cfg/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    state = GOING_TO_POSITION
    topology = {}
    while running(demo_mode, step, 6000):
        traci.simulationStep()
        # when reaching 60 seconds, reset the simulation when in demo_mode
        if demo_mode and step == 600000:
            start_sumo("../cfg/freeway.sumo.cfg", True)
            step = 1
            random.seed(1)

        if step > START_STEP and step % 10 == 1:
            # simulate vehicle communication every 100 ms
            communicate(plexe, topology)
            distanceP = get_distance(plexe, "p.0", "p.1")

            # print(distanceP)

            pass

        if step == 100 + START_STEP:
            # at 1 second, let the joiner get closer to the platoon
            topology = get_in_position(plexe, JOINER, FRONT_JOIN, topology)

        if state == GOING_TO_POSITION and step > START_STEP:
            # when the distance of the joiner is small enough, let the others
            # open a gap to let the joiner enter the platoon
            if get_distance(plexe, JOINER, FRONT_JOIN) < JOIN_DISTANCE + 1:
                state = OPENING_GAP
                topology = open_gap(plexe, BEHIND_JOIN, JOINER, topology, N_VEHICLES)

        if state == OPENING_GAP:
            # when the gap is large enough, complete the maneuver
            if get_distance(plexe, BEHIND_JOIN, FRONT_JOIN) > JOIN_DISTANCE + 5:
                plexe.set_fixed_lane(JOINER, LANE_NUM, safe=False)
                plexe.set_active_controller(JOINER, CACC)
                plexe.set_path_cacc_parameters(JOINER, distance=DISTANCE)
                plexe.set_active_controller(BEHIND_JOIN, CACC)
                plexe.set_path_cacc_parameters(BEHIND_JOIN, distance=DISTANCE)
                topology = reset_leader(BEHIND_JOIN, topology, N_VEHICLES)
                state = COMPLETED
                DELAY_TIME = step

        if state == COMPLETED and step == DELAY_TIME + 1300:
            print(topology)
            for i in range(1, JOIN_POSITION):
                plexe.add_member(LEADER, "p.%d" % i, i)
            plexe.add_member(LEADER, JOINER, JOIN_POSITION)
            for i in range(JOIN_POSITION, 6):
                plexe.add_member(LEADER, "p.%d" % i, i+1)
            

        if state == COMPLETED and step % 1000 == 1:
            lane_id = traci.vehicle.getLaneID(LEADER)
            limit_speed = traci.lane.getMaxSpeed(lane_id)
            # traci.vehicle.setSpeed(LEADER,limit_speed)

            plexe.enable_auto_lane_changing(LEADER, True)
            print(plexe.get_radar_data(LEADER))

            print(limit_speed)
            # plexe.set_cc_desired_speed(LEADER,limit_speed)
            


        if step > START_STEP and step % 1000 == 1:
            # dicv = traci.multientryexit.getLastStepVehicleNumber("e3_0")
            # dicv = traci.multientryexit.getLastIntervalVehicleSum("e3_0")

            # print(dicv)
            pass

        if step < 100 and step % 3 == 0:
            pass
        else:
            pass
        if step == START_STEP:
            topology = add_vehicles(plexe, N_VEHICLES, 90, real_engine)
            traci.gui.trackVehicle("View #0", LEADER)
            traci.gui.setZoom("View #0", 2000)
        step += 1

    traci.close()


if __name__ == "__main__":
    main(True, False)
