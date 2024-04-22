# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    vertical_profiles.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/04/19 21:06:36 by daniloceano       #+#    #+#              #
#    Updated: 2024/04/19 21:20:14 by daniloceano      ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as colors
import cmocean as cmo

# Load the data
variable = 'MFD'
results_file = f"ATMOS-BUD_Akara-subset_ERA5_track/{variable}.csv"

df = pd.read_csv(results_file, index_col=0)
df.columns = pd.to_datetime(df.columns)
df.index = df.index/100

fig, ax = plt.subplots(figsize=(12, 6))
ax.invert_yaxis()

# Resample the data to daily means
df_T = df.T
df_T.index = pd.to_datetime(df_T.index)
daily_mean = df_T.resample('2D').mean().T
daily_mean = daily_mean.iloc[10:]

# Plot daily means
for time_step in range(len(daily_mean.columns)):
    print(df.columns[time_step])

    # Select the time step
    time = daily_mean.columns[time_step]
    data = daily_mean[time]

    # Plot the data
    ax.plot(data, data.index, label=time.strftime('%Y-%m-%d'))

ax.axvline(x=0, color='black', linestyle='--', zorder=1)

# Labels and title
ax.set_title(variable)
ax.set_ylabel('Pressure Level (hPa)')  # assuming units are in Pascal, adjust as needed
ax.legend()

plt.xticks(rotation=45)
plt.savefig(f"figures/{variable}.png")
    