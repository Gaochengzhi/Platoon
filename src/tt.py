import os

L_VEHICLES = int(os.environ["LV"])
N_VEHICLES = int(os.environ["NV"])

VEHSPERHOUR = int(os.environ["VSUM"])
CACC_MPRS = float(os.environ["MPRS"])

import shutil

copy_cfg = (
    str(VEHSPERHOUR)
    + "|"
    + str(CACC_MPRS)
    + "|"
    + str(N_VEHICLES)
    + "|"
    + str(L_VEHICLES)
)
shutil.copytree("../cfg", copy_cfg, dirs_exist_ok=True)


shutil.copytree(copy_cfg + "/data", "../data/" + copy_cfg, dirs_exist_ok=True)


shutil.rmtree(copy_cfg)
