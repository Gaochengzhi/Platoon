import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

import os
import pandas as pd

root_dir = '.'
data = pd.read_csv('./collection.csv')
# file_suffix = os.environ["f"]
# folder_name = os.environ["folder"]
# core = int(os.environ["core"])
# yl = os.environ["y"]

fn = os.environ["f"]
x_name = os.environ['x']
def clean_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
clean_folder(fn)

grouped_data = data.groupby(['volume', 'heave_veh'])
for name, group in grouped_data:
    volume, heave_veh = name
    plt.figure()
    plt.ylim(18,30)
    if "lane" in x_name:
        plt.ylim(0,1300)
    for cacc_mprs, group_data in group.groupby('cacc_mprs'):
        xs = group_data['cacc_len']
        ys = group_data[x_name]

        if len(xs)==1:
            xs = (3,4,5,6)
            ys = (ys.values[0],ys.values[0],ys.values[0],ys.values[0])
        xs, ys = zip(*sorted(zip(xs, ys)))
        plt.plot(xs, ys, label=cacc_mprs)
    plt.title(f'Volume={int(volume)}, Passenger Vehicle={heave_veh}')
    plt.xlabel('CACC Length')
    plt.ylabel('Mean Speed')
    plt.legend(loc="upper right")
    # plt.show()
    plt.savefig(fn+"/"+str(volume)+str(heave_veh)+'.png')
    plt.close()




def run_in_process(file_path):
    print(file_path)
    df = pd.read_csv(file_path)
    mask = (df['step'] >= start) & (df['step'] <= end)
    df = df[mask]
    grouped = df.groupby('idv')
    plt.figure(figsize=(13, 8), dpi=300)
    for name, group in grouped:
        color = 'green'
        # print(group['idv'])
        if all(group['idv'].astype(str).str.startswith("p.")):
            color = 'red'
        elif all(group['lane_index'] < 1 & group['idv'].astype(str).str.isalnum()):
            color = 'blue'
        else:
            color = 'green'
        plt.plot(group[xl], group[yl], label=name, linewidth=0.5, color=color)
