"""
count_all_modalities.py
Author: Maggie Jacoby
date: 2021-01-13

"""

import os
import csv
import sys
from glob import glob
import numpy as np
import pandas as pd
from datetime import datetime

from gen_argparse import *
from my_functions import *


### Populate dictionary with all days used in database
start_end_dict = {
    'H1': [['2019-11-26',' 2019-12-25']], 
    'H2': [['2019-03-13', '2019-03-29']], 
    'H3': [['2019-07-23', '2019-08-04'], ['2019-08-15', '2019-09-05']], 
    # 'H3': [['2019-07-23', '2019-07-25']], 
    'H4': [['2019-05-01', '2019-05-12'], ['2019-05-17', '2019-05-21']],
    'H5': [['2019-06-07', '2019-06-21']],
    'H6': [['2019-10-12', '2019-11-02'], ['2019-11-20', '2019-12-05']]}

def database_days():
    all_days_dict = {}

    for home in start_end_dict:
        home_st = start_end_dict[home]
        all_days = []

        for st in home_st:
            start, end = st[0], st[1]
            pd_days = pd.date_range(start=start, end=end).tolist()
            days = [d.strftime('%Y-%m-%d') for d in pd_days]
            all_days.extend(days)
        all_days_dict[home] = all_days
    
    return all_days_dict

################

def count_audio(days_to_use, data_path, hub=None, max_files=8640):
    print(f'Counting audio on {hub}...')
    dates = glob(os.path.join(data_path, '2019-*'))
    dates = [f for f in dates if os.path.basename(f) in days_to_use]

    counts = {}
    for day in dates:
        all_times = glob(os.path.join(day, '*/*.csv'))
        set_times = set([os.path.basename(x).split('_')[1] for x in all_times])
        dt = datetime.strptime(os.path.basename(day), '%Y-%m-%d').date()
        totals = len(set_times)/max_files
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts


def count_images(days_to_use, data_path, hub=None, max_files=86400):
    print(f'Counting images on {hub}...')
    dates = glob(os.path.join(data_path, '2019-*'))
    dates = [f for f in dates if os.path.basename(f) in days_to_use]

    counts = {}
    for day in dates:
        all_times = glob(os.path.join(day, '*/*.png'))
        set_times = set([os.path.basename(x).split('_')[1] for x in all_times])
        dt = datetime.strptime(os.path.basename(day), '%Y-%m-%d').date()
        totals = len(set_times)/max_files
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts

def count_dark(days_to_use, data_path, hub, max_files=86400):
    print(f'Counting dark images on {hub}...')
    data_path = os.path.join(data_path, f'{H_num}_{hub}_DARKIMAGES')
    dates = glob(os.path.join(data_path, '2019-*'))
    dates = [f for f in dates if os.path.basename(f).split('_')[0] in days_to_use]

    counts = {}
    for day in dates:
        all_times = pd.read_csv(day)
        all_times = all_times.values.tolist()
        set_times = set([x[0].split(' ')[1] for x in all_times])
        dt = datetime.strptime(os.path.basename(day).split('_')[0], '%Y-%m-%d').date()
        totals = len(set_times)/max_files
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts


def count_env(days_to_use, data_path, hub=None, max_seconds=8640):
    print(f'Counting environmental on {hub}...')
    dates = glob(os.path.join(data_path, '*_2019-*'))
    dates = [f for f in dates if os.path.basename(f).split('_')[2].strip('.csv') in days_to_use]

    counts = {}
    for day in dates:
        cols_to_read = ['timestamp', 'tvoc_ppb', 'temp_c', 'rh_percent', 'light_lux', 'co2eq_ppm', 'dist_mm']
        day_data = pd.read_csv(day, usecols=cols_to_read, index_col='timestamp')
        # complete_data = day_data.dropna(axis=0, how='all')
        complete_data = day_data.dropna(axis=0, how='any')
        dt = datetime.strptime(os.path.basename(day).split('_')[2].strip('.csv'), '%Y-%m-%d').date()
        totals = len(complete_data)/max_seconds
        counts[dt] = float(f'{totals:.2}') if totals != 0 else 0.0

    return counts





def get_count_df(mod_name, mod_lookup, sub_path=None):
    counts = {}
    for hub in hubs[:]:
        if sub_path:
            data_path = os.path.join(path, hub, sub_path)
        else:
            data_path = os.path.join(path, hub)
        counts[f'{hub}_{mod_name}'] = mod_lookup(days_to_use=dbDays, data_path=data_path, hub=hub)
    df = pd.DataFrame(counts)
    return df




if __name__ == '__main__':

    dbDays = database_days()[H_num]
    
    print(f'{H_num}: {len(dbDays)} days')

    env_counts = get_count_df(sub_path='processed_env/CSV-raw', mod_name='Env', mod_lookup=count_env)
    audio_counts = get_count_df(sub_path='processed_audio/audio_csv', mod_name='Audio', mod_lookup=count_audio)
    image_counts = get_count_df(sub_path='img-downsized', mod_name='Img', mod_lookup=count_images)
    dark_counts = get_count_df(mod_name='Img_dark', mod_lookup=count_dark)
    print('Done counting.')

    combined_img = pd.DataFrame()
    for col1, col2 in zip(sorted(image_counts.columns), sorted(dark_counts.columns)):
        if col1.split('_')[0] != col2.split('_')[0]:
            print(f'mismatch! Can not combine {col1} and {col2}')
            continue
        combined_img[col1] = image_counts[col1] + dark_counts[col2]

    # env_counts.to_csv('~/Desktop/env_df_counts.csv')
    # image_counts.to_csv('~/Desktop/image_df_counts.csv')
    # audio_counts.to_csv('~/Desktop/audio_df_counts.csv')
    # dark_counts.to_csv('~/Desktop/dark_df_counts.csv')


    full_counts = pd.concat([audio_counts, dark_counts, combined_img, env_counts], axis=1)
    full_counts = full_counts.reindex(sorted(full_counts.columns), axis=1)

    full_counts.to_excel(f'~/Desktop/CompleteSummaries/new_summary_code/{H_num}_counts.xlsx')
