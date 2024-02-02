import numpy as np
import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

import os
import pandas as pd

# data directory
root_dir = "."
# csv file suffix
fs = os.environ["f"]
# time range
start = int(os.environ["from"]) * 100
end = int(os.environ["to"]) * 100

# max mutitask number
core = int(os.environ["core"])

xl = os.environ["x"]
yl = os.environ["y"]

# saved folder name
folder_name = fs + "_" + xl + "_" + yl


def clean_folder():
    os.chdir("../res")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    os.chdir("../data")


def run_in_process(file_path):
    print(file_path)
    df = pd.read_csv(file_path)
    mask = (df["step"] >= start) & (df["step"] <= end)
    df = df[mask]
    grouped = df.groupby("idv")
    plt.figure(figsize=(6, 1.8), dpi=300)
    for name, group in grouped:
        color = "green"
        if all(group["idv"].astype(str).str.startswith("p.")):
            color = "red"
            ls = "dotted"
        elif all(group["lane_index"] < 1 & group["idv"].astype(str).str.isalnum()):
            color = "blue"
            ls = "dashed"
        else:
            color = "green"
            ls = "solid"
        plt.plot(
            group[xl], group[yl], linestyle=ls, label=name, linewidth=0.5, color=color
        )
    # plt.legend()
    plt.gca().xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, pos: "{:.0f}".format(x / 100))
    )
    filename = file_path.replace("/", "|").replace(".", "") + ".png"
    tmp = filename.split("|")
    vol = tmp[1]
    cacc_mpr = tmp[2]
    cacc_len = tmp[3]
    truck_ratio = tmp[4]

    # plt.title(f"Density: {vol} veh/h, Truck ratio: {truck_ratio[1]}0%\nCACC MPR: {cacc_mpr[1]}0%, CACC Size: {cacc_len} veh")
    # plt.title(f"Density: {vol} veh/h, Truck ratio: {truck_ratio[1]}0%")
    # if yl == "idv_speed":
    plt.ylim(-3, -18)
    # plt.xlabel("Time (s)")
    # plt.ylabel("Speed (m/s)")
    plt.xticks([])
    plt.yticks([])
    plt.savefig("../res/" + folder_name + "/" + filename, bbox_inches="tight")
    plt.clf()
    plt.close()
    pass


def main():
    clean_folder()
    count = 0
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file_path.endswith(fs + ".csv"):
                p = multiprocessing.Process(target=run_in_process, args=(file_path,))
                count += 1
                p.start()
                if count == core:
                    # exit()
                    p.join()
                    count = 0


if __name__ == "__main__":
    main()
