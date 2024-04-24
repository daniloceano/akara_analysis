
import os
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob
from lorenz_phase_space.phase_diagrams import Visualizer

# Read periods data
df_periods = pd.read_csv("LEC_Akara-subset_ERA5_track/periods.csv", index_col=0)

figures_directory = "figures/compare_methodologies"
os.makedirs(figures_directory, exist_ok=True)

adjust = 0.05
periods = True

results_path = glob(f"LEC_*")

for result_path in results_path:

    result_file = glob(f"{result_path}/Akara*.csv")[0]
    exp_name = os.path.basename(result_path).split("_")[-1]

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
    plot_filename = f"LPS_periods_{exp_name}.png"

    # Generate the phase diagram
    lps.plot_data(
        x_axis=df['Ck'].tolist(),
        y_axis=df['Ca'].tolist(),
        marker_color=df['Ge'].tolist(),
        marker_size=df['Ke'].tolist(),
    )

    # Save the final plot
    figure_path = os.path.join(figures_directory, plot_filename)
    plt.savefig(figure_path)
    print(f"Figure saved to: {figure_path}")

