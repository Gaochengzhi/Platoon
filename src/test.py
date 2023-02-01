#!/usr/bin/env python
from math import sqrt
import random
import os
import sys
import random
import matplotlib.pyplot as plt
import numpy as np
import re
import csv
from utils import check_sumo_env

check_sumo_env()
import traci
from traci import StepListener, constants as tc, vehicle
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

L_VEHICLES = 3
N_VEHICLES = 6

VEHSPERHOUR = 1600 * 5
CACC_MPRS = 0.2

CACC_INSERT_RATE = CACC_MPRS / N_VEHICLES
TOTAL_TIME = int(60 * 60 * 100)
VEH_PER_STEP = int(TOTAL_TIME / VEHSPERHOUR)

END_EDGE_ID = "E5"

# inter-vehicle distance

START_STEP = 0
# cruising speed
SPEED = 30
# lane_number latoon insert
LANE_NUM = 2
CHECK_ALL = 0b01111  # SpeedMode
LAN_CHANGE_MODE = 0b011001011000
#                   0123456789
ptype_list = []


def extract_number(string):
    match = re.search(r"p.(\d+)", string)
    if match:
        return int(match.group(1))
    return None


def cacc_turn(cacc_mprs=CACC_INSERT_RATE):
    r = random.random()
    if r < cacc_mprs:
        return True
    return False


def set_random_platoon_type(
    distribution=[L_VEHICLES, N_VEHICLES - L_VEHICLES], vtype_list=["ptruck", "pcar"]
):
    ptype_list.clear()
    for _i in range(distribution[0]):
        vtype_num = str(random.randint(0, 999))
        ptype_list.append(vtype_list[0] + vtype_num)
    for _i in range(distribution[1]):
        vtype_num = str(random.randint(0, 999))
        ptype_list.append(vtype_list[1] + vtype_num)


def get_random_vtype(distribution=[0.8, 0.9, 1], vtype_list=["car", "truck", "bus"]):
    r = random.random()
    vtype_suffix = ""
    j = 0
    for i in distribution:
        if r < i:
            vtype_suffix = vtype_list[j]
            break
        j += 1
    vtype_num = random.randint(0, 999)
    return vtype_suffix + str(vtype_num)


def get_depart_lane_and_speed(distribution=0.2):
    r = random.random()
    if r < distribution:
        return "merge_route", str(random.uniform(14, 16.6))
    else:
        return "platoon_route", str(random.uniform(30, 33.3))


def get_length(type_index):
    if type_index > 0:
        i = type_index
    else:
        i = type_index + 1
    return float(traci.vehicletype.getLength(ptype_list[i]))


def cacc_spacing(type_index):
    if type_index > 0:
        space = get_length(type_index)
    else:
        space = get_length(type_index + 1)
    return sqrt(space) * 1.5


def get_position(init_position):
    current = init_position

    def f(length):
        nonlocal current
        current -= length
        return current

    return f


def add_vehicles(plexe, start_num, end_num, position, lane_num, real_engine=False):
    topology = {}
    set_random_platoon_type()
    get_insert_postion = get_position(position)
    leader_num = ""
    desire_speed = random.randint(29, 32)
    for i in range(end_num - start_num):
        v_num = start_num + i
        vid = "p.%d" % v_num
        if i == 0:
            leader_num = vid
        insert_postion = get_insert_postion(cacc_spacing(i - 1) + get_length(i - 1))
        add_platooning_vehicle(
            plexe,
            vid,
            insert_postion,
            lane_num,
            SPEED,
            cacc_spacing(i - 1),
            real_engine,
            ptype_list[i],
        )
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.set_cc_desired_speed(vid, desire_speed)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            # traci.vehicle.setLaneChangeMode(vid, LAN_CHANGE_MODE)
        else:
            plexe.set_active_controller(vid, CACC)
            # plexe.enable_auto_feed(vid, True, LEADER, "p.%d" % (i - 1))
            plexe.add_member(leader_num, vid, i)
        if i > 0:
            topology[vid] = {
                "front": "p.%d" % (start_num + i - 1),
                "leader": leader_num,
            }
        plexe.set_fixed_lane(vid, lane_num, safe=False)
        plexe.enable_auto_lane_changing(leader_num, True)
    return topology


def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    start_sumo("../case2/freeway.sumo.cfg", False)
    plexe = Plexe()
    traci.addStepListener(plexe)
    step = 0
    front_ptr = 0
    random.seed(7)
    vid_list = 0
    insert_gap = 0

    extent_step = False
    veh_per_step = VEH_PER_STEP
    platoon_list = []
    f = open("../case2/data/fcd.out.csv", "w")
    writer = csv.writer(f)
    while running(demo_mode, step, TOTAL_TIME):
        traci.simulationStep()
        if demo_mode and step == TOTAL_TIME:
            f.close()
            exit()
            # start_sumo("../case2/freeway.sumo.cfg", True)
            # step = 0
            # front_ptr = 0
            # random.seed(7)
            # vid_list = 0
            # insert_gap = 0

        # if step > START_STEP:  # remove collision
        #     colliding_vehicles = traci.simulation.getCollidingVehiclesIDList()
        #
        #     if colliding_vehicles:
        #         p_veicle_list = [
        #             vehicle
        #             for vehicle in colliding_vehicles
        #             if vehicle.startswith("p.")
        #         ]  # find platoon vehicle
        #
        #         print(colliding_vehicles)
        #         if p_veicle_list:
        #             for vid in p_veicle_list:
        #                 vid_index = extract_number(vid)
        #                 platoon_index = int(vid_index / N_VEHICLES)
        #                 platoon_list[platoon_index] = {}
        #     for car in colliding_vehicles:
        #         traci.vehicle.remove(car, 0)

        if step > START_STEP and step % 1000 == 1:  # remove pass by cacc vehicles
            vehicle_list = traci.edge.getLastStepVehicleIDs("E2")

            if vehicle_list:
                p_veicle_list = [
                    vehicle for vehicle in vehicle_list if vehicle.startswith("p.")
                ]  # find platoon vehicle

                vehicle_sum = len(vehicle_list)
                p_vehicle_sum = len(p_veicle_list)

                for idv in vehicle_list:
                    id_speed = traci.vehicle.getSpeed(idv)
                writer.writerow([1, 2, 3, 4, 5])

        if step > START_STEP and step % 10 == 1:  # remove pass by cacc vehicles
            vehicle_list = traci.edge.getLastStepVehicleIDs(END_EDGE_ID)
            if vehicle_list:
                p_veicle_list = [
                    vehicle for vehicle in vehicle_list if vehicle.startswith("p.")
                ]  # find platoon vehicle
                if p_veicle_list:
                    for vid in p_veicle_list:
                        vid_index = extract_number(vid)
                        platoon_index = int(vid_index / N_VEHICLES)
                        platoon_list[platoon_index] = {}
                        for i in range(
                            platoon_index * N_VEHICLES,
                            platoon_index * N_VEHICLES + N_VEHICLES,
                        ):
                            try:
                                traci.vehicle.remove("p.%d" % (i), 0)
                            except Exception as e:
                                pass
            for items in platoon_list:
                if items:
                    communicate(plexe, items)
                pass

        if step > START_STEP and step % 10 == 1:  # communicate cacc
            pass

        if step >= START_STEP and insert_gap % veh_per_step == 1:
            if cacc_turn():
                if not extent_step:
                    veh_per_step = int(veh_per_step * N_VEHICLES)
                    extent_step = True
                    insert_gap = 1
                veh_lane = random.randint(0, 3)
                veh_pos = random.randint(112, 114)
                topology = add_vehicles(
                    plexe,
                    front_ptr,
                    front_ptr + N_VEHICLES,
                    veh_pos,
                    veh_lane,
                    real_engine,
                )
                front_ptr += N_VEHICLES
                platoon_list.append(topology)
                pass
            else:
                if extent_step:
                    veh_per_step = int(veh_per_step / N_VEHICLES)
                    extent_step = False
                veh_type = get_random_vtype()
                depart_route, depart_speed = get_depart_lane_and_speed()
                depart_pos = str(random.randint(99, 100))
                traci.vehicle.add(
                    vehID=str(vid_list),
                    routeID=depart_route,
                    typeID=veh_type,
                    departSpeed=depart_speed,
                    departPos=depart_pos,
                    departLane="random",
                )
                vid_list += 1

        step += 1
        insert_gap += 1

    traci.close()


if __name__ == "__main__":
    main(True, False)
