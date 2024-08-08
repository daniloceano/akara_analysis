
import os
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from lorenz_phase_space.phase_diagrams import Visualizer

# Read periods data
df_periods = pd.read_csv("LEC_Akara-subset2_ERA5_track/periods.csv", index_col=0)

adjust = 0.05
periods = True


result_file = "LEC_Akara-subset2_ERA5_track/Akara-subset2_ERA5_track_results.csv"

lps = Visualizer(
    LPS_type='mixed',
    zoom=True,
    x_limits=[-6, 3],
    y_limits=[-1, 1],
    color_limits=[-2, 3],
    marker_limits=[280000, 505000],
)

df_energetics = pd.read_csv(result_file, index_col=0)
# Create a new DataFrame to store the means
df = pd.DataFrame(index=df_periods.index, columns=df_energetics.columns)
# Compute means for each period
for idx, period in df_periods.iterrows():
    start, end = period['start'], period['end']
    period_data = df_energetics.loc[start:end]
    df.loc[idx] = period_data.mean()  
# Use the new DataFrame
df.index = range(len(df))
# Adjust figure name
plot_filename = "LPS_periods_track.png"

# Generate the phase diagram
lps.plot_data(
    x_axis=df['Ck'].tolist(),
    y_axis=df['Ca'].tolist(),
    marker_color=df['Ge'].tolist(),
    marker_size=df['Ke'].tolist(),
)

plt.ylim(-0.2, 0.3)

# Save the final plot
figure_path = os.path.join("Banner_CPAM", plot_filename)
plt.savefig(figure_path)
print(f"Figure saved to: {figure_path}")

