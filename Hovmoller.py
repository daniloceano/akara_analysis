# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Hovmoller.py                                       :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2024/04/19 21:06:29 by daniloceano       #+#    #+#              #
#    Updated: 2024/04/22 14:24:07 by daniloceano      ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import pandas as pd
import cmocean.cm as cmo
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

# Set up directories
figures_path = 'figures/'
os.makedirs(figures_path, exist_ok=True)

# Variables to plot
variables = ['AdvHTemp', 'ResT', 'AdvHZeta', 'Omega']

for variable in variables:
    file = f'../ATMOS-BUD_Results/sample1_ERA5_track/{variable}.csv'
    df = pd.read_csv(file, index_col=0)
    df.columns = pd.to_datetime(df.columns)
    df.columns = df.columns.strftime('%Y-%m-%d %H:%M')
    df.index = df.index/100

    # Plot hovmollers
    fig, ax = plt.subplots(figsize=(10, 5))
    # Adjusts limits of colormap to max, min and zero
    norm = colors.TwoSlopeNorm(vmin=df.to_numpy().min(), vcenter=0, vmax=df.to_numpy().max())

    # plot hovmoller diagram
    fig, ax = plt.subplots(figsize=(10,10))
    im = ax.contourf(df.columns, df.index, df.values, cmap=cmo.balance, levels=7)
    cbar = fig.colorbar(im)

    # invert y-axis
    ax.invert_yaxis()

    # format x-axis as date and rotate tick labels
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    ax.tick_params(axis='x', labelrotation=45)

    # Set title and axis labels
    ax.set_title(f'{variable}', fontsize=16)
    ax.set_ylabel('Pressure [hPa]', fontsize=14)

    # edit colorbar legend
    cbar.ax.tick_params(labelsize=10)

    plt.savefig(figures_path + f'hovmoller_{variable}.png', dpi=300)

figures_directory = "figures"
os.makedirs(figures_directory, exist_ok=True)
figure_path = os.path.join(figures_directory, f"hovmoller_{variable}.png")
plt.savefig(figure_path)
print(f"Figure saved to: {figure_path}")
