# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Hovmoller.py                                       :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/04/19 21:06:29 by daniloceano       #+#    #+#              #
#    Updated: 2024/04/19 21:07:29 by daniloceano      ###   ########.fr        #
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

# Prepare the plot
fig, ax = plt.subplots(figsize=(12, 6))

# Normalize the data limits for the colorbar
imin = df.min(numeric_only=True).min()
imax = df.max(numeric_only=True).max()
absmax = np.amax([np.abs(imin), imax])
norm = colors.TwoSlopeNorm(vcenter=0, vmin=-absmax * 0.8, vmax=absmax * 0.8)

levels = np.linspace(-absmax, absmax, 10)

# Create the Hovmöller diagram
c = ax.contourf(df.columns, df.index.astype(float), df, cmap=cmo.cm.balance,
                norm=norm, levels=levels, extend='both')

# Set the format of the date on the x-axis
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # adjust interval as needed
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

ax.invert_yaxis()

# Adding color bar
plt.colorbar(c, ax=ax, label='Values')

# Labels and title
ax.set_title(variable)
ax.set_ylabel('Pressure Level (hPa)')  # assuming units are in Pascal, adjust as necessary

plt.xticks(rotation=45)
plt.tight_layout()

figures_directory = "figures"
os.makedirs(figures_directory, exist_ok=True)
figure_path = os.path.join(figures_directory, f"hovmoller_{variable}.png")
plt.savefig(figure_path)
print(f"Figure saved to: {figure_path}")
