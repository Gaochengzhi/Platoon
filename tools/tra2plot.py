

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






def run_in_process(file_path):
    print(file_path)
    folder_name = file_path.split("/")[-2]
    file_name = file_path.split("/")[-1]
    os.chdir(folder_name)
    df = pd.read_csv(file_name)
    # filter time range
    mask = (df['step'] >= start) & (df['step'] <= end)
    df = df[mask]

    speed_stats = df.groupby('idv')['idv_speed'].agg(['mean', 'std'])
    lane_changes = df.groupby('idv')['lane_index'].nunique()

# combine the results into a single DataFrame
    result = pd.concat([speed_stats, lane_changes], axis=1)


    result.to_csv("mean|std"+fs+"st.csv", index=True)
    

def main():
    count = 0
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file_path.endswith(fs+'.csv'):
                p = multiprocessing.Process(
                    target=run_in_process, args=(file_path,))
                count += 1
                p.start()
                if count == core:
                    p.join()
                    count = 0


if __name__ == '__main__':
    main()
