from utils import check_sumo_env, sumolib, traci
check_sumo_env()


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



def main(demo_mode, real_engine, setter=None):
    # used to randomly color the vehicles
    random.seed(1)
    record_time = 0
    start_sumo("", False)
    plexe = Plexe()
    traci.addStepListener(plexe)

