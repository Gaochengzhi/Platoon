import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import numpy as np
from pysal.explore import esda
from pysal.lib import weights

# Define the parameters
A_values = [3500, 4500, 5500, 6500, 7500]
B_values = [0.0, 0.2, 0.4, 0.6]
C_values = {0.0: 0, 0.2: 5, 0.4: 5, 0.6: 5}
D_value = 0.6

# Create a 5x4 grid of subplots
fig, axs = plt.subplots(5, 4, figsize=(20, 20))

# Iterate over the parameters
for i, A in enumerate(A_values):
    for j, B in enumerate(B_values):
        C = C_values[B]
        D = D_value
        # Construct the file name
        folder_name = f"{A}|{B}|{C}|{D}"
        file_name = os.path.join("..", "data", folder_name, "fcd.in.csv")

        # Load the data
        df = pd.read_csv(file_name)

        # Filter the data to only include steps from 1500s to 3500s
        df = df[(df['step'] >= 1500 * 100) & (df['step'] <= 3500 * 100)]

        # Group by vehicle id and calculate mean and std of speed
        grouped_idv = df.groupby('idv').agg({'idv_speed': ['mean', 'std']}).reset_index()
        df['step_piece'] = pd.cut(df['step'], bins=10, labels=False)
        # Group by idv and step_piece, calculate mean and std of speed
        grouped_idv_piece = df.groupby(['idv', 'step_piece']).agg({'idv_speed': ['mean', 'std']}).reset_index()

        # Prepare data for Moran's I
        data = grouped_idv_piece[('idv_speed', 'mean')].values.reshape(-1, 1)
        data = np.concatenate((data, grouped_idv_piece[('idv_speed', 'std')].values.reshape(-1, 1)), axis=1)

        # Perform Moran's I calculation
        data = np.nan_to_num(data, nan=0.0, posinf=np.finfo(np.float32).max, neginf=np.finfo(np.float32).min)

        scaler = StandardScaler()
        data = scaler.fit_transform(data)

        # Create a spatial weights matrix. Here, we assume that the data is ordered in a 2D grid.
        # If this is not the case, you will need to create the weights matrix differently.
        w = weights.lat2W(data.shape[0], data.shape[1])

        # Calculate Moran's I
        moran = esda.Moran(data, w)

        # Print filename and measure
        print(f"File: {file_name}, Moran's I: {3+moran.I}")

        # Plot Moran's I on the corresponding subplot
        colors = ['red' if str(idv).startswith('p.') else 'blue' if lane == 0 else 'green'
          for idv, lane in zip(grouped_idv_piece['idv'], df['lane_index'])]
        sizes = [3 if str(idv).startswith('p.') else 2 for idv in grouped_idv_piece['idv']]
        axs[i, j].scatter(data[:, 0], data[:, 1], c=colors, s=sizes)
        axs[i, j].set_title(f"A={A}, B={B}, C={C}, D={D}\nMoran's I: {moran.I:.4f}")

# Display the figure
plt.tight_layout()
plt.savefig("moran.png")
