#!/usr/bin/env python3
"""
Script to create vertical profiles of Ck sub-terms for different cyclone development stages.
Compares Ck_1, Ck_2, Ck_3, Ck_4, and Ck_5 terms across four stages: Incipient, Intensification, Mature, and Decay.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Define paths
base_path = Path('./akara1_track')
data_path = base_path / 'results_vertical_levels'
output_path = Path("./")
output_path.mkdir(exist_ok=True)

# Define development stages (dates in UTC)
stages = {
    'Incipient': ('2024-02-14 21:00:00', '2024-02-16 09:00:00'),
    'Intensification': ('2024-02-16 09:00:00', '2024-02-19 15:00:00'),
    'Mature': ('2024-02-19 15:00:00', '2024-02-20 09:00:00'),
    'Decay': ('2024-02-20 09:00:00', '2024-02-22 21:00:00')
}

# Define Ck sub-terms
ck_terms = ['Ck_1', 'Ck_2', 'Ck_3', 'Ck_4', 'Ck_5']

# Colors for each term (matching the style of the reference figure)
colors = {
    'Ck_1': '#1f77b4',  # Blue - similar to local temperature tendency
    'Ck_2': '#ff7f0e',  # Orange - similar to horizontal temperature advection  
    'Ck_3': '#ffdd57',  # Yellow - similar to vertical motion effect
    'Ck_4': '#87ceeb',  # Light blue - similar to diabatic heating
    'Ck_5': '#808080',  # Gray - additional term
}

# Labels for each term
labels = {
    'Ck_1': r'$C_k^A$',
    'Ck_2': r'$C_k^A$',
    'Ck_3': r'$C_k^B$',
    'Ck_4': r'$C_k^C$',
    'Ck_5': r'$C_k^D$',
}

def load_ck_data(term):
    """Load data for a specific Ck sub-term."""
    file_path = data_path / f'{term}_pressure_level.csv'
    df = pd.read_csv(file_path)
    df['valid_time'] = pd.to_datetime(df['valid_time'])
    df.set_index('valid_time', inplace=True)
    return df

def compute_stage_mean(df, start_time, end_time):
    """Compute mean profile for a specific time period."""
    # Filter data for the time period
    mask = (df.index >= start_time) & (df.index <= end_time)
    stage_data = df.loc[mask]
    
    # Compute mean across time
    mean_profile = stage_data.mean(axis=0)
    
    # Convert pressure levels from Pa to hPa and get as array
    pressure_levels = np.array([float(col) / 100 for col in mean_profile.index])
    values = mean_profile.values
    
    return pressure_levels, values

def create_vertical_profiles():
    """Create figure with vertical profiles for all stages and terms."""
    
    # First, compute all mean profiles to find global min/max
    all_stage_data = {}
    global_min = np.inf
    global_max = -np.inf
    
    for stage_name, (start_time, end_time) in stages.items():
        stage_profiles = {}
        for term in ck_terms:
            df = load_ck_data(term)
            pressure, values = compute_stage_mean(df, start_time, end_time)
            values_per_day = values
            stage_profiles[term] = (pressure, values_per_day)
            
            # Update global min/max
            valid_values = values_per_day[~np.isnan(values_per_day)]
            if len(valid_values) > 0:
                global_min = min(global_min, valid_values.min())
                global_max = max(global_max, valid_values.max())
        
        all_stage_data[stage_name] = stage_profiles
    
    # Make x-axis symmetric
    x_limit = max(abs(global_min), abs(global_max))
    print(f'Global min: {global_min:.2f} K/day')
    print(f'Global max: {global_max:.2f} K/day')
    print(f'Symmetric x-axis limit: ±{x_limit:.2f} K/day')
    
    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharey=True, sharex=True)
    fig.suptitle('Barotropic Conversion Sub-terms - Akará Track', fontsize=14, fontweight='bold')
    
    # Flatten axes for easier iteration
    axes_flat = axes.flatten()
    
    # Iterate over stages
    for idx, (stage_name, stage_profiles) in enumerate(all_stage_data.items()):
        ax = axes_flat[idx]
        
        # Plot each Ck sub-term
        for term in ck_terms:
            pressure, values_per_day = stage_profiles[term]
            
            # Plot
            ax.plot(values_per_day, pressure, 
                   label=labels[term], 
                   color=colors[term], 
                   linewidth=2)
        
        # Add vertical line at x=0
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
        
        # Formatting
        ax.set_title(f'({chr(65+idx)}) {stage_name}', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Set symmetric x-axis limits
        ax.set_xlim(-x_limit, x_limit)
        
        # Set y-axis (1000 hPa at bottom, 100 hPa at top)
        ax.set_ylim(1000, 100)
        
        # Labels for bottom row
        if idx >= 2:
            ax.set_xlabel('(W m$^{-2}$)', fontsize=11)
        
        # Labels for left column
        if idx % 2 == 0:
            ax.set_ylabel('Pressure (hPa)', fontsize=11)
    
    # Add legend below the figure
    handles, labels_list = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels_list, loc='lower center', 
              bbox_to_anchor=(0.5, -0.02), ncol=5, 
              frameon=True, fontsize=11)
    
    # Adjust layout to make room for legend
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    # Save figure
    output_file = output_path / 'ck_subterms_vertical_profiles.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f'Figure saved to: {output_file}')
    
    # Show figure
    plt.show()

if __name__ == '__main__':
    print('Creating vertical profiles for Ck sub-terms...')
    print(f'Data path: {data_path}')
    print(f'Output path: {output_path}')
    print()
    
    # Check if data files exist
    for term in ck_terms:
        file_path = data_path / f'{term}_pressure_level.csv'
        if not file_path.exists():
            print(f'WARNING: File not found: {file_path}')
        else:
            print(f'Found: {file_path.name}')
    
    print()
    print('Development stages:')
    for stage_name, (start, end) in stages.items():
        print(f'  {stage_name}: {start} to {end}')
    
    print()
    create_vertical_profiles()
