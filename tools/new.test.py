import os
import numpy as np
import pandas as pd
from multiprocessing import Pool, Lock
from numpy.fft import rfft, fftfreq
from scipy.stats import zscore
from pysal.lib import weights
import esda
from sklearn.preprocessing import StandardScaler
import csv
from multiprocessing import Manager
import pywt
from scipy.signal import butter, filtfilt
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import zscore

def clean_stat_file():
    file_path = 'quantify_data.csv'
    if os.path.exists(file_path):
        os.remove(file_path)

def write_to_file(data, lock):
    with lock:
        with open('quantify_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

def filter_df(file_name):
    df = pd.read_csv(file_name)
    df = df[(df['step'] >= 1500 * 100) & (df['step'] <= 3500 * 100)]
    return df

def operation_one(df):
    mean_speed_per_vehicle = df.groupby('idv')['idv_speed'].mean()
    return np.mean(mean_speed_per_vehicle)


def operation_two(df):
  cutoff = 0.2
  b, a = butter(3, cutoff, 'highpass', fs=5)
  energies = []
  for vid in df['idv'].unique():
    accel = df[df['idv'] == vid]['idv_acc'].values
    padlen = min(3, len(accel)//2) 
    smooth_accel = filtfilt(b, a, accel, padlen=padlen)
    coeffs = pywt.wavedec(smooth_accel, 'db4', level=1)
    coeff_energies = [np.sum(np.abs(c)**2) for c in coeffs[1:]]
    avg_energy = np.mean(coeff_energies)
    energies.append(avg_energy)
  return np.mean(energies) 
def operation_four(df):
    lane_changes = df.groupby('idv')['lane_index'].apply(lambda x: (x.diff() != 0).sum())
    return np.sum(lane_changes)-len(lane_changes)
def operation_three(df):
    df['step_piece'] = pd.cut(df['step'], bins=10, labels=False)
    grouped_idv_piece = df.groupby(['idv', 'step_piece']).agg({'idv_speed': ['mean', 'std'], 'idv_lane_pos': ['mean', 'std']}).reset_index()

    speed_dispersion = grouped_idv_piece['idv_speed', 'std'].mean()
    lane_dispersion = grouped_idv_piece['idv_lane_pos', 'std'].mean()
    
    # Calculate an overall measure of dispwersion
    dispersion = np.sqrt(speed_dispersion**2 + lane_dispersion**2)
    # dispersion = speed_dispersion
    return dispersion

def operation_five(df):
    # Filtering out extraordinary data points (outliers) based on idv_lane_pos
 
    df_filtered = df
    
    # Check if 50% or more of all vehicles have a speed below 10 (defining this as "congested")
    total_vehicle_count = len(df_filtered)
    slow_vehicle_count = len(df_filtered[df_filtered['idv_speed'] < 13])
    
    if slow_vehicle_count / total_vehicle_count < 0.2:
        return 0  # If less than 50% of vehicles are slow, there's no congestion, return 0

    # If congestion exists, calculate the length of the congestion
    lower_pos = np.percentile(df_filtered['idv_lane_pos'], 5)
    upper_pos = np.percentile(df_filtered['idv_lane_pos'], 95)

    congestion_length = upper_pos - lower_pos

    return congestion_length





def process_folder(folder_name, lock):
    data = []
    data.extend(folder_name.split('/')[2].split('|'))
    # for file_name in ["fcd.before.csv", "fcd.in.csv", "fcd.out.csv"]:
    for file_name in ["fcd.before.csv", "fcd.in.csv", "fcd.out.csv"]:
        full_path = os.path.join(folder_name, file_name)
        df = filter_df(full_path)
        df = df[df['idv_speed'] > 0.1]
        data.append(operation_one(df))
        data.append(operation_two(df))
        data.append(operation_three(df))
        data.append(operation_four(df))
        data.append(operation_five(df))
    write_to_file(data, lock)

if __name__ == "__main__":
    clean_stat_file()
    volume_values = [3500, 4500, 5500, 6500, 7500]
    # volume_values = [4500, 6500, 7500]
    cacc_mpr_values = [0.0, 0.2, 0.4, 0.6]
    cacc_size_values = [3,4,5,6]
    truck_ratio_values = [0.2, 0.4, 0.6]
    lock = Lock()
    with Manager() as manager:
            lock = manager.Lock()
            with open('quantify_data.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['volume', 'cacc_mpr', 'cacc_size', 'truck_ratio', \
                    'before_meanspeed', 'before_frequncy', 'before_moran', 'before_change','before_len',\
                    'in_meanspeed', 'in_frequncy', 'in_moran', 'in_change','in_len',\
                    'out_meanspeed', 'out_frequncy', 'out_moran','out_change', 'out_len',])

            with Pool(24) as p:
                tasks = []
                for volume in volume_values:
                    for cacc_mpr in cacc_mpr_values:
                        if cacc_mpr == 0.0:
                            cacc_sizes = [0]
                        else:
                            cacc_sizes = cacc_size_values
                        for cacc_size in cacc_sizes:
                            for truck_ratio in truck_ratio_values:
                                folder_name = f"../data/{volume}|{cacc_mpr}|{cacc_size}|{truck_ratio}"
                                tasks.append(p.apply_async(process_folder, (folder_name, lock)))
                for task in tasks:
                    task.get()