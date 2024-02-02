import os
import asyncio
from multiprocessing import Pool
import pandas as pd
from scipy.fft import rfft, fftfreq
import esda
from sklearn.preprocessing import StandardScaler
import weights
from pysal.lib import weights
import csv
from multiprocessing import Lock

import numpy as np


def clean_stat_file():
    file_path = 'stat.csv'
    if os.path.exists(file_path):
        os.remove(file_path)


def compute_mean_speed(df):
    return df['idv_speed'].mean()


def compute_frequency(df):
    vehicle_ids = df['idv'].unique()
    trajectory_mean_values = []
    for vehicle in vehicle_ids:
        vehicle_data = df[df['idv'] == vehicle]
        accel = vehicle_data['idv_acc'].values
        fft_accel = rfft(accel)
        freqs = fftfreq(accel.shape[-1], d=0.1)
        lower_bound = 0.2 * np.max(freqs)
        upper_bound = 0.8 * np.max(freqs)
        filtered_indices = np.where(
            (freqs >= lower_bound) & (freqs <= upper_bound))
        filtered_fft_accel = fft_accel[filtered_indices]
        filtered_freqs = freqs[filtered_indices]
        if filtered_fft_accel.size != 0:
            max_freq = filtered_freqs[np.argmax(np.abs(filtered_fft_accel))]
            trajectory_mean_values.append(max_freq)
        else:
            trajectory_mean_values.append(0)
    return np.sum(trajectory_mean_values)


def compute_moran(df):
    df = df[(df['step'] >= 1500 * 100) & (df['step'] <= 3500 * 100)]

    grouped_idv = df.groupby('idv').agg(
        {'idv_speed': ['mean', 'std']}).reset_index()
    df['step_piece'] = pd.cut(df['step'], bins=10, labels=False)
    grouped_idv_piece = df.groupby(['idv', 'step_piece']).agg(
        {'idv_speed': ['mean', 'std']}).reset_index()
    data = grouped_idv_piece[('idv_speed', 'mean')].values.reshape(-1, 1)
    data = np.concatenate(
        (data, grouped_idv_piece[('idv_speed', 'std')].values.reshape(-1, 1)), axis=1)
    data = np.nan_to_num(data, nan=0.0, posinf=np.finfo(
        np.float32).max, neginf=np.finfo(np.float32).min)
    scaler = StandardScaler()
    data = scaler.fit_transform(data)
    w = weights.lat2W(data.shape[0], data.shape[1])
    moran = esda.Moran(data, w)
    return moran.I


async def process_folder(folder_name, lock):
    before_ms = compute_mean_speed(pd.read_csv(
        os.path.join(folder_name, "fcd.before.csv")))
    before_freq = compute_frequency(pd.read_csv(
        os.path.join(folder_name, "fcd.before.csv")))
    before_moran = compute_moran(pd.read_csv(
        os.path.join(folder_name, "fcd.before.csv")))

    in_ms = compute_mean_speed(pd.read_csv(
        os.path.join(folder_name, "fcd.in.csv")))
    in_freq = compute_frequency(pd.read_csv(
        os.path.join(folder_name, "fcd.in.csv")))
    in_moran = compute_moran(pd.read_csv(
        os.path.join(folder_name, "fcd.in.csv")))

    out_ms = compute_mean_speed(pd.read_csv(
        os.path.join(folder_name, "fcd.out.csv")))
    out_freq = compute_frequency(pd.read_csv(
        os.path.join(folder_name, "fcd.out.csv")))
    out_moran = compute_moran(pd.read_csv(
        os.path.join(folder_name, "fcd.out.csv")))

    volume, cacc_mpr, cacc_size, truck_ratio = folder_name.split(
        '/')[-1].split('|')

    with lock:
        with open('stat.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([volume, cacc_mpr, cacc_size, truck_ratio,
                            before_ms, before_freq, before_moran,
                            in_ms, in_freq, in_moran,
                            out_ms, out_freq, out_moran])


async def main():
    clean_stat_file()
    lock = Lock()
    semaphore = asyncio.Semaphore(24)
    volume_values = [3500, 4500, 5500, 6500, 7500]
    cacc_mpr_values = [0.0, 0.2, 0.4, 0.6]
    cacc_size_values = [3, 4, 5, 6]
    truck_ratio_values = [0.2, 0.4, 0.6]

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
                    tasks.append(process_folder(folder_name, lock))

    with Pool(24) as p:
        p.map(asyncio.to_thread, tasks)

if __name__ == "__main__":
    asyncio.run(main())
