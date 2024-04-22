# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    vertical_profiles.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/04/19 21:06:36 by daniloceano       #+#    #+#              #
#    Updated: 2024/04/22 14:26:08 by daniloceano      ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as colors
import cmocean as cmo

# Set up directories
figures_path = 'figures/'
os.makedirs(figures_path, exist_ok=True)

# Variables to plot
variables = ['AdvHTemp', 'ResT', 'AdvHZeta', 'Omega']

for variable in variables:
    file = f"ATMOS-BUD_Akara-subset_ERA5_track/{variable}.csv"
    df = pd.read_csv(file, index_col=0)

    # Mak daily means
    df = df.T
    df.index = pd.to_datetime(df.index)
    df_daily = df.resample('D').mean()
    df = df_daily.T
    df.columns = df.columns.strftime('%Y-%m-%d')
    df.index = df.index/100

    # Plot vertical profiles 
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df, df.index, label=df.columns, linewidth=2)
    ax.axvline(0, color='k', linewidth=0.5, zorder=2)
    ax.grid(True, linestyle='--', linewidth=0.5, zorder=1)
    ax.invert_yaxis()
    ax.set_ylabel('Pressure [hPa]')
    ax.title.set_text(f'{variable}')
    plt.legend()
    plt.savefig(figures_path + f'vertical_profile_{variable}.png', dpi=300)