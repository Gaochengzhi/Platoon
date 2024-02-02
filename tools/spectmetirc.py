import os
import pandas as pd 
import numpy as np
from scipy.fft import rfft, fftfreq,rfftfreq
from multiprocessing import Pool 
import scipy.stats as stats

# Define the parameters
A_values = [3500, 4500, 5500, 6500, 7500]
B_values = [0.0, 0.2, 0.4, 0.6]  
C_values = {0.0: 0, 0.2: 5, 0.4: 5, 0.6: 5}
D_value = 0.4

# Initialize a list to store the mean values for each file
mean_values = []


def process_file(args):
    i, A, B, C, D = args
    folder_name = f"{A}|{B}|{C}|{D}"
    file_name = os.path.join("..", "data", folder_name, "fcd.in.csv")
    df = pd.read_csv(file_name)
    df = df[(df['step'] >= 1500 * 100) & (df['step'] <= 3500 * 100)]
    vehicle_ids = df['idv'].unique()
    trajectory_mean_values = []
    for vehicle in vehicle_ids:
        vehicle_data = df[df['idv'] == vehicle]
        accel = vehicle_data['idv_acc'].values
        fft_accel = rfft(accel)
        freqs = fftfreq(accel.shape[-1], d=0.1)
        # Define the frequency range
        lower_bound = 0.1 * np.max(freqs)
        upper_bound = 0.9 * np.max(freqs)
        # Filter the frequencies
        filtered_indices = np.where((freqs >= lower_bound) & (freqs <= upper_bound))
        filtered_fft_accel = fft_accel[filtered_indices]
        filtered_freqs = freqs[filtered_indices]
        
        # Check if filtered_fft_accel is not empty
        if filtered_fft_accel.size != 0:
            # Find the max frequency in the filtered range
            max_freq = filtered_freqs[np.argmax(np.abs(filtered_fft_accel))]
            trajectory_mean_values.append(max_freq)
        else:
            trajectory_mean_values.append(0)
            print(f"No frequencies found in the specified range for vehicle {vehicle}. Skipping...")
        
    file_mean = np.sum(trajectory_mean_values)
    return (f"File: {file_name}, Mean: {file_mean}", file_mean)
if __name__ == "__main__":
    args = []
    for i, A in enumerate(A_values):
        for j, B in enumerate(B_values):
            C = C_values[B]
            D = D_value
            args.append((i, A, B, C, D))
            
    with Pool(24) as p:
        mean_values = p.map(process_file, args)
    
    # Print the output messages in order
    for message, mean_value in mean_values:
        print(message)

