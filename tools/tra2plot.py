

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
    table = df[mask]
# Group by idv and calculate mean and standard deviation of idv_speed
    speed_stats = table.groupby('idv')['idv_speed'].agg(['mean', 'std'])

# Calculate the number of lane changes for each idv
    lane_changes = table.groupby('idv')['lane_index'].apply(lambda x: (x.diff() != 0).sum())

# Combine the speed and lane change statistics into a single dataframe
    stats = pd.concat([speed_stats, lane_changes], axis=1)

# Save the results to a CSV file

    stats.to_csv("mean|std"+fs+"st.csv", index=True)



# combine the results into a single DataFrame
    # result = pd.concat([speed_stats, lane_changes], axis=1)


    

def main():
    count = 0
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file_path.endswith(fs+'.csv'):

                print(file_path)
                # run_in_process(file_path)
                # exit()
                p = multiprocessing.Process(
                    target=run_in_process, args=(file_path,))
                count += 1
                p.start()
                if count == core:
                    p.join()
                    count = 0


if __name__ == '__main__':

    os.chdir('../data')
    main()
