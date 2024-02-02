#!/usr/bin/env python
from math import sqrt
import random
import os
import sys
import time
import re
import csv
from utils import check_sumo_env
import shutil

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

LARGE_VEH = float(os.environ["LV"])
TYPE_DISTRIBUTION = [LARGE_VEH, 1]
PLV_LENGTH = int(os.environ["NV"])

VPH = int(os.environ["VSUM"]) * 5
CACC_MPRS = float(os.environ["MPRS"])
if PLV_LENGTH != 0:
    CACC_INSERT_RATE = CACC_MPRS / PLV_LENGTH
else:
    CACC_INSERT_RATE = 0

TOTAL_TIME = int(60 * 60 * 100)
VEH_PER_STEP = int(TOTAL_TIME / VPH)

END_EDGE_ID = "E7"

# inter-vehicle distance

START_STEP = 0
# lane_number latoon insert
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


def set_random_platoon_type(cacc_length=PLV_LENGTH):
    ptype_list.clear()
    for i in range(cacc_length):
        ptype_list.append("p" + get_random_vtype())
    ptype_list.sort(reverse=True)


def get_random_vtype(distribution=TYPE_DISTRIBUTION, vtype_list=["truck", "car"]):
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


def get_depart_lane_and_speed(distribution=0.2 / (1 - CACC_MPRS)):
    r = random.random()
    if r < distribution:
        return "merge_route", str(random.uniform(14, 16.6))
    else:
        return "platoon_route", str(random.uniform(25, 26))


def get_length(type_index):
    if type_index > 0:
        i = type_index
    else:
        i = type_index + 1
    return float(traci.vehicletype.getLength(ptype_list[i]))


def get_acc(type_index):
    if type_index > 0:
        i = type_index
    else:
        i = type_index + 1
    return float(traci.vehicletype.getAccel(ptype_list[i]))


def get_tau(type_index):
    if type_index > 0:
        i = type_index
    else:
        i = type_index + 1
    return float(traci.vehicletype.getTau(ptype_list[i]))


def cacc_spacing(type_index):
    if type_index > 0:
        space = get_length(type_index)
    else:
        space = get_length(type_index + 1)
    return sqrt(space) - 1.5


def get_position(init_position):
    current = init_position

    def f(length):
        nonlocal current
        current -= length
        return current

    return f


def get_veh_info(edge_id, writer, step):

    vehicle_list = traci.edge.getLastStepVehicleIDs(edge_id)

    if vehicle_list:
        p_veicle_list = [
            vehicle for vehicle in vehicle_list if vehicle.startswith("p.")
        ]  # find platoon vehicle
        vehicle_sum = len(vehicle_list)
        p_vehicle_sum = len(p_veicle_list)
        for idv in vehicle_list:
            idv_speed = traci.vehicle.getSpeed(idv)
            idv_acc = traci.vehicle.getAcceleration(idv)
            idv_lane_pos = traci.vehicle.getLanePosition(idv)
            idv_type = traci.vehicle.getTypeID(idv)
            idv_lane = traci.vehicle.getLaneIndex(idv)

            writer.writerow(
                [
                    idv,
                    step,
                    idv_type,
                    round(idv_speed, 4),
                    round(idv_acc, 4),
                    round(idv_lane_pos, 4),
                    idv_lane,
                    vehicle_sum,
                    p_vehicle_sum,
                ]
            )


def init_csv_file(path):
    f = open(path, "w")
    writer = csv.writer(f)
    writer.writerow(
        [
            "idv",
            "step",
            "idv_type",
            "idv_speed",
            "idv_acc",
            "idv_lane_pos",
            "lane_index",
            "vehicle_sum",
            "p_vehicle_sum",
        ]
    )
    return f, writer


def add_vehicles(plexe, start_num, end_num, position, lane_num, real_engine=False):
    topology = {}
    set_random_platoon_type()
    get_insert_postion = get_position(position)
    leader_num = ""
    desire_speed = random.randint(25, 26)
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
            desire_speed,
            # cacc_spacing(i - 1),
            0,
            real_engine,
            ptype_list[i],
        )
        traci.vehicle.setSpeedMode(vid, 0)
        plexe.set_cc_desired_speed(vid, desire_speed)
        if i == 0:
            plexe.set_active_controller(vid, ACC)
            # traci.vehicle.setLaneChangeMode(vid, LAN_CHANGE_MODE)
            pass
        else:
            plexe.set_active_controller(vid, CACC)
            # plexe.enable_auto_feed(vid, True, leader_num, "p.%d" % (start_num+i - 1))
            plexe.add_member(leader_num, vid, i)
        if i > 0:
            topology[vid] = {
                "front": "p.%d" % (start_num + i - 1),
                "leader": leader_num,
            }
        traci.vehicle.setLaneChangeMode(vid, 1621)
        plexe.set_fixed_lane(vid, lane_num, safe=False)
        plexe.enable_auto_lane_changing(leader_num, True)
    return topology


def gene_config():
    copy_cfg = (
        str(VPH)
        + "|"
        + str(round(CACC_MPRS, 1))
        + "|"
        + str(PLV_LENGTH)
        + "|"
        + str(round(LARGE_VEH, 1))
    )
    shutil.copytree("../cfg", copy_cfg, dirs_exist_ok=True)
    return copy_cfg


def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    cfg_file = gene_config()
    start_sumo(cfg_file + "/freeway.sumo.cfg", False)
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

    f1, before_writer = init_csv_file(cfg_file + "/data/fcd.before.csv")
    f2, in_writer = init_csv_file(cfg_file + "/data/fcd.in.csv")
    f3, after_writer = init_csv_file(cfg_file + "/data/fcd.out.csv")

    while running(demo_mode, step, TOTAL_TIME + 1):
        traci.simulationStep()
        if demo_mode and step == TOTAL_TIME:
            f1.close()
            f2.close()
            f3.close()
            shutil.copytree(
                cfg_file + "/data", "../data/" + cfg_file, dirs_exist_ok=True
            )
            shutil.rmtree(cfg_file)
            time.sleep(9)
            traci.close()
            quit()
            break
        if step > START_STEP and step % 20 == 1:  # remove pass by cacc vehicles
            get_veh_info("E3", before_writer, step)
            get_veh_info("E4", in_writer, step)
            get_veh_info("E5", after_writer, step)

        if step > START_STEP and step % 10 == 1:  # remove pass by cacc vehicles
            vehicle_list = traci.edge.getLastStepVehicleIDs(END_EDGE_ID)
            if vehicle_list:
                p_veicle_list = [
                    vehicle for vehicle in vehicle_list if vehicle.startswith("p.")
                ]  # find platoon vehicle
                if p_veicle_list:
                    for vid in p_veicle_list:
                        vid_index = extract_number(vid)
                        platoon_index = int(vid_index / PLV_LENGTH)
                        platoon_list[platoon_index] = {}
                        for i in range(
                            platoon_index * PLV_LENGTH,
                            platoon_index * PLV_LENGTH + PLV_LENGTH,
                        ):
                            try:
                                traci.vehicle.remove("p.%d" % (i), 0)
                            except Exception as e:
                                pass

            for items in platoon_list:
                if items:
                    communicate(plexe, items)

                pass

        if step >= START_STEP and insert_gap % veh_per_step == 1:
            if cacc_turn():
                if not extent_step:
                    veh_per_step = int(veh_per_step * PLV_LENGTH)
                    extent_step = True
                    insert_gap = 1
                veh_lane = random.randint(0, 3)
                veh_pos = random.randint(112, 114)
                topology = add_vehicles(
                    plexe,
                    front_ptr,
                    front_ptr + PLV_LENGTH,
                    veh_pos,
                    veh_lane,
                    real_engine,
                )
                front_ptr += PLV_LENGTH
                platoon_list.append(topology)
                pass
            else:
                if extent_step:
                    veh_per_step = int(veh_per_step / PLV_LENGTH)
                    extent_step = False
                veh_type = get_random_vtype()
                depart_route, depart_speed = get_depart_lane_and_speed()
                depart_pos = str(random.randint(98, 101))
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
