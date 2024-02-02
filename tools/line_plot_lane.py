import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

import os
import pandas as pd

root_dir = '.'
data = pd.read_csv('../res/collection.csv')

fn = os.environ["f"]
x_name = os.environ['x']
def clean_folder(folder_name):
    os.chdir("../res")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    os.chdir("../data")

clean_folder(fn)

grouped_data = data.groupby(['volume', 'heave_veh'])
for name, group in grouped_data:
    volume, heave_veh = name
    plt.figure()
    # if not "lane" in x_name:
    #     plt.ylim(8,30)
    #plt.ylim(16,26)
    plt.figure(figsize=(5, 4), dpi=300)
    markers = ['o', 's', 'd', '^']
    for i, (cacc_mprs, group_data) in enumerate(group.groupby('cacc_mprs')):
        xs = group_data['cacc_len']
        ys = group_data[x_name]

        if len(xs)==1:
            xs = (3,4,5,6)
            ys = (ys.values[0],ys.values[0],ys.values[0],ys.values[0])
        xs, ys = zip(*sorted(zip(xs, ys)))
        plt.plot(xs, ys, label="CACC MPR "+str(format(cacc_mprs,'.0%')), marker=markers[i])
        # plt.plot(xs, ys, marker='o',label=cacc_mprs)
    plt.title(f'Density: {int(volume)} veh/h, Truck ratio: {str(format(heave_veh,".0%"))}')
    plt.grid()
    plt.xticks([3, 4, 5, 6])
    plt.ylim(200,2000)
    # plt.yticks([x for x in range(16,27,2)])
    plt.xlabel('CACC Size (vehicles)',fontsize=12)
    plt.ylabel('Mean Speed (m/s)',fontsize=12)
    plt.legend(loc="best")
    # plt.show()
    plt.savefig("../res/"+fn+"/"+str(volume)+str(heave_veh)+'.png')
    plt.close()
