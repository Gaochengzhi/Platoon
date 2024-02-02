import os
import pandas as pd 
import numpy as np
from scipy.fft import rfft, fftfreq,rfftfreq
from multiprocessing import Pool 
import scipy.stats as stats
import csv

def clean_stat_file():
    file_path = 'stat.csv'
    if os.path.exists(file_path):
        os.remove(file_path)

# Initialize a list to store the mean values for each file
mean_values = []

def write_to_file(data, lock):
    with lock:
        with open('quantify_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)


def process_folder(args):
    (volume,cacc_mpr,cacc_size,truck_ratio) = args
    folder_name = f"../data/{volume}|{cacc_mpr}|{cacc_size}|{truck_ratio}/"
    print(folder_name)
    file_name = os.path.join(folder_name, "fcd.in.csv")
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
    clean_stat_file()
    args = []
    volume_values = [3500, 4500, 5500, 6500, 7500]
    cacc_mpr_values = [0.0, 0.2, 0.4, 0.6]
    cacc_size_values = [3,4,5,6] 
    truck_ratio_values = [0.2, 0.4, 0.6]
    with open('stat.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(["volume", "cacc_mpr", "cacc_size", "truck_ratio", 
                            "before_ms", "before_freq", "before_moran",
                            "in_ms", "in_freq", "in_moran",
                            "out_ms", "out_freq", "out_moran"])
    for volume in volume_values:
        for cacc_mpr in cacc_mpr_values:
            if cacc_mpr == 0.0:
                cacc_sizes = [0]
            else:
                cacc_sizes = cacc_size_values
            for cacc_size in cacc_sizes:
                for truck_ratio in truck_ratio_values:
                    folder_name = f"../data/{volume}|{cacc_mpr}|{cacc_size}|{truck_ratio}" 
                    args.append((volume,cacc_mpr,cacc_size,truck_ratio))
            
    with Pool(24) as p:
        mean_values = p.map(process_folder, args)
    

