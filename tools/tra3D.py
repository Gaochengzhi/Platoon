from mpl_toolkits import mplot3d

import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt

import os
import pandas as pd

# data directory
root_dir = '.'
# csv file suffix
fs = os.environ["f"]
# time range
start = int(os.environ["from"])*100
end = int(os.environ["to"])*100

# max mutitask number
core = int(os.environ["core"])

xl = os.environ["x"]
yl = os.environ["y"]

# saved folder name
folder_name = fs+xl+yl



def clean_folder():
    os.chdir("../res")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    os.chdir("../data")


def run_in_process(file_path):
    print(file_path)
    df = pd.read_csv(file_path)
    mask = (df['step'] >= start) & (df['step'] <= end)
    df = df[mask]
    grouped = df.groupby('idv')
    # plt.figure(figsize=(13, 8), dpi=300)
    ax = plt.axes(projection='3d')
    for name, group in grouped:
        color = 'green'
        if all(group['idv'].astype(str).str.startswith("p.")):
            color = 'red'
        elif all(group['lane_index'] < 1 & group['idv'].astype(str).str.isalnum()):
            color = 'blue'
        else:
            color = 'green'
        ax.plot3D(group[xl], group[yl],group['lane_index'], label=name, linewidth=0.5, color=color)

    # plt.legend()
    filename = file_path.replace("/", "|").replace(".", "") + ".png"
    plt.title(filename)
    if yl != "lane_index":
        plt.ylim(0,33)
    plt.xlabel(xl)
    plt.ylabel(yl)
    plt.show()
    
    # plt.savefig('../res/'+folder_name+'/'+filename)
    # plt.clf()
    # plt.close()
    # pass


def main():
    clean_folder()
    count = 0
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            
            if file_path.endswith(fs+'.csv'):
                run_in_process(file_path)

                pass
                p = multiprocessing.Process(
                    target=run_in_process, args=(file_path,))
                count += 1
                p.start()
                if count == core:
                    # exit()
                    p.join()
                    count = 0


if __name__ == '__main__':
    main()
