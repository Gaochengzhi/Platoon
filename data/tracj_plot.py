import pandas as pd
import matplotlib.pyplot as plt

import os
import pandas as pd

root_dir = '.'

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        file_path = os.path.join(subdir, file)
        if file_path.endswith('.csv'):
            print(file_path)
            df = pd.read_csv(file_path)

            start_time = 30000 # start of time period
            end_time = 59000 # end of time period
            mask = (df['step'] >= start_time) & (df['step'] <= end_time)
            df = df[mask]
            grouped = df.groupby('idv')
            for name, group in grouped:
                plt.plot(group['step'], group['idv_lane_pos'], label=name)
            plt.show()
            plt.legend()
            plt.xlabel('Time')
            plt.ylabel('Position')
            filename = file_path.replace("/", "|") + ".png"
            plt.savefig(filename)
            plt.clf()
            pass

# 1. Import the CSV file into a Pandas DataFrame

# 2. Filter the DataFrame to include only the desired time period

# 3. Group the data by the 'vid' column

# 4. Plot the data for each vehicle


