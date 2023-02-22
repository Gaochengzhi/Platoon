

import csv
import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

import os
import numpy as np
from pathlib import Path

# data directory
root_dir = '.'
# csv file suffix

# saved folder name


data_file = Path("./collection.csv")
main_folder = '.'

def clean_file():
    if data_file.exists():
        # if the file exists, delete its contents
        open(data_file, 'w').close()
    else:
        # if the file does not exist, create it
        data_file.touch()
    pass


def run_in_process(file_path,f):
    volume= file_path.split("|")[0]
    cacc_mprs=file_path.split("|")[1]
    cacc_len=file_path.split("|")[2]
    heave_veh=file_path.split("|")[3]
    row = [
        volume,
        cacc_mprs,
        cacc_len,
        heave_veh,
        "speed_mean",
        "count",
        "e0_speed_mean",
        "e0_speed_std",
        "e0_count",
        "e0_lane_change",
        "e1_speed_mean",
        "e1_speed_std",
        "e1_count",
        "e1_lane_change",
        "e2_speed_mean",
        "e2_speed_std",
        "e2_count",
        "e2_lane_change",
    ]
    file_list = [f for f in os.listdir() if f.startswith('mean|std') and f.endswith('.csv')]
    print(file_list)
    for file in file_list:
        df = pd.read_csv(file)
        mean_mean = df['mean'].mean()
        std_mean = df['mean'].std()
        row_count = df.shape[0]-1
        sum_lane_index = df['lane_index'].sum() - row_count
        position = 6
        if "before" in file:
            pass
        elif "in" in file:
            position = 10
        else:
            position = 14
        row[position]=mean_mean
        row[position+1]=std_mean
        row[position+2]=row_count
        row[position+3]=sum_lane_index
    # mean speed
    row[4] = np.mean([row[6],row[10],row[14]])
    # count
    row[5] = np.sum([row[8],row[8],row[8]])
    

            

    f.writerow(row)


    # df = pd.read_csv(file_name)


    # mask = (df['step'] >= start) & (df['step'] <= end)
    # df = df[mask]
    pass

def create_csv_header(f):
    writer = csv.writer(f)
    row = (
        "volume",
        "cacc_mprs",
        "cacc_len",
        "heave_veh",
        "speed_mean",
        "count",
        "e0_speed_mean",
        "e0_speed_std",
        "e0_count",
        "e0_lane_change",
        "e1_speed_mean",
        "e1_speed_std",
        "e1_count",
        "e1_lane_change",
        "e2_speed_mean",
        "e2_speed_std",
        "e2_count",
        "e2_lane_change"
    )
    writer.writerow(row)
    return writer

def main():
    clean_file()
    f = open(data_file, "w+")
    writer = create_csv_header(f)
    # count = 0
    for folder in os.listdir(main_folder):
        if folder[0].isdigit():
            os.chdir(folder)
            run_in_process(folder,writer)
            # exit()
            os.chdir("..")
    # for subdir, dirs, files in os.walk(root_dir):
    #     for file in files:
    #         file_path = os.path.join(subdir, file)
    #         if file_path.endswith(fs+'.csv'):
    #             run_in_process(file_path,f)
    f.close()


if __name__ == '__main__':
    main()
