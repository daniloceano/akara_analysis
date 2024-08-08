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

file = "LEC_Akara-subset2_ERA5_track/results_vertical_levels/Ck_level.csv"
df = pd.read_csv(file, index_col=0)
df.index = pd.to_datetime(df.index)
df.columns = df.columns.astype(float) / 100

# Transpose the DataFrame for correct dimensions
df = df.T

# Plot hovmollers
fig, ax = plt.subplots(figsize=(10, 10))

norm = colors.TwoSlopeNorm(vmin=df.to_numpy().min(), vcenter=0, vmax=df.to_numpy().max())

# plot hovmoller diagram
im = ax.contourf(df.columns, df.index, df, cmap=cmo.curl, levels=10, norm=norm, extend='both')
cbar = fig.colorbar(im)

# invert y-axis
ax.invert_yaxis()

# format x-axis as date and rotate tick labels
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
ax.tick_params(axis='x', labelrotation=45)

# Set title and axis labels
ax.set_title('Ck', fontsize=16)
ax.set_ylabel('Pressure [hPa]', fontsize=14)

# edit colorbar legend
cbar.ax.tick_params(labelsize=10)

# Save the figure
figure_path = os.path.join(figures_path, 'hovmoller_Ck.png')
plt.savefig(figure_path, dpi=300)
print(f"Figure saved to: {figure_path}")
