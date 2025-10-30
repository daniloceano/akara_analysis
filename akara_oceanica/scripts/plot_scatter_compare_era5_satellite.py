"""
Compare ERA5 wave data with satellite altimetry observations.

This script creates a scatter plot comparing ERA5 significant wave height
with satellite measurements, including:
- Density-based coloring (turbo colormap)
- 1:1 reference line
- Linear regression line
- Statistics (R², RMSE, bias)
"""

import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.stats import gaussian_kde, linregress
from datetime import timedelta
import xarray as xr
import glob
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Latitude and longitude of point 1 (degrees)
        lat2, lon2: Latitude and longitude of point 2 (degrees)
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Earth radius in kilometers
    r = 6371.0
    
    return c * r


def load_era5_data(era5_file):
    """
    Load ERA5 reanalysis data.
    
    Args:
        era5_file: Path to ERA5 NetCDF file
        
    Returns:
        DataFrame with columns: datetime, lat, lon, swh
    """
    print(f"📂 Loading ERA5 data from {os.path.basename(era5_file)}...")
    
    ds = xr.open_dataset(era5_file)
    
    # Detect dimension names (ERA5 can use different conventions)
    time_dim = 'valid_time' if 'valid_time' in ds.dims else 'time'
    lat_dim = 'latitude' if 'latitude' in ds.dims else 'lat'
    lon_dim = 'longitude' if 'longitude' in ds.dims else 'lon'
    
    print(f"   Converting to DataFrame (this may take a moment)...")
    
    # Convert to DataFrame in one shot - fastest approach
    df = ds['swh'].to_dataframe().reset_index()
    
    # Rename columns to standard names
    rename_dict = {}
    if time_dim in df.columns:
        rename_dict[time_dim] = 'datetime'
    if lat_dim in df.columns:
        rename_dict[lat_dim] = 'lat'
    if lon_dim in df.columns:
        rename_dict[lon_dim] = 'lon'
    
    df = df.rename(columns=rename_dict)
    
    # Remove NaN values
    df = df.dropna(subset=['swh'])
    
    # Convert longitude from 0-360 to -180-180
    df.loc[df['lon'] > 180, 'lon'] -= 360
    
    # Ensure datetime is timezone-naive (to match satellite data)
    if hasattr(df['datetime'].dtype, 'tz') and df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    
    print(f"   ✓ Loaded {len(df):,} ERA5 grid points")
    print(f"   ✓ Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"   ✓ Spatial range: lat [{df['lat'].min():.2f}, {df['lat'].max():.2f}], lon [{df['lon'].min():.2f}, {df['lon'].max():.2f}]")
    print(f"   ✓ SWH range: {df['swh'].min():.2f} to {df['swh'].max():.2f} m")
    
    ds.close()
    
    return df


def load_satellite_data(data_dir):
    """
    Load all satellite data from CSV files.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        DataFrame with all satellite data
    """
    print("\n📂 Loading satellite data...")
    
    satellite_dirs = [
        'AltiKa', 'Cryosat-2', 'HY-2B', 'Jason-3', 
        'Saral', 'Sentinel-3A', 'Sentinel-3B', 'Sentinel-6A'
    ]
    
    all_data = []
    
    for sat_name in satellite_dirs:
        sat_dir = data_dir / sat_name
        if not sat_dir.exists():
            continue
        
        csv_files = list(sat_dir.glob('*.csv'))
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df['satellite'] = sat_name
                df['datetime'] = pd.to_datetime(df['time'])
                
                # Rename columns to standard names
                if 'latitude' in df.columns:
                    df['lat'] = df['latitude']
                if 'longitude' in df.columns:
                    df['lon'] = df['longitude']
                
                # Convert longitude to -180 to 180 if needed
                if 'lon' in df.columns:
                    df.loc[df['lon'] > 180, 'lon'] = df.loc[df['lon'] > 180, 'lon'] - 360
                
                # Select relevant columns
                if all(col in df.columns for col in ['datetime', 'lat', 'lon', 'value']):
                    df_clean = df[['datetime', 'lat', 'lon', 'value', 'satellite']].copy()
                    df_clean.rename(columns={'value': 'swh_sat'}, inplace=True)
                    all_data.append(df_clean)
            except Exception as e:
                print(f"⚠️  Error loading {csv_file.name}: {e}")
                continue
    
    if not all_data:
        raise ValueError("No satellite data found!")
    
    sat_df = pd.concat(all_data, ignore_index=True)
    sat_df = sat_df.sort_values('datetime').reset_index(drop=True)
    
    # Remove timezone information to avoid comparison issues
    if sat_df['datetime'].dt.tz is not None:
        sat_df['datetime'] = sat_df['datetime'].dt.tz_localize(None)
    
    print(f"✅ Loaded {len(sat_df)} satellite observations from {len(all_data)} files")
    print(f"   Satellites: {', '.join(sat_df['satellite'].unique())}")
    print(f"   Date range: {sat_df['datetime'].min()} to {sat_df['datetime'].max()}")
    
    return sat_df


def match_era5_satellite(era5_df, sat_df, max_distance_km=50, max_time_hours=1):
    """
    Match ALL satellite observations with closest ERA5 grid points.
    
    For each satellite observation, finds the closest ERA5 point in space and time.
    
    Args:
        era5_df: DataFrame with ERA5 data
        sat_df: DataFrame with satellite data
        max_distance_km: Maximum distance for spatial matching (km)
        max_time_hours: Maximum time difference for temporal matching (hours)
        
    Returns:
        DataFrame with matched pairs
    """
    print(f"\n🔍 Matching satellite observations with ERA5 grid points...")
    print(f"   Processing {len(sat_df):,} satellite observations...")
    print(f"   Spatial window: {max_distance_km} km")
    print(f"   Temporal window: ±{max_time_hours} hour(s)")
    
    matches = []
    
    # Process each satellite observation
    n_processed = 0
    for sat_idx, sat_row in sat_df.iterrows():
        n_processed += 1
        if n_processed % 10000 == 0:
            print(f"   ... processed {n_processed:,} / {len(sat_df):,} observations")
        
        # Find ERA5 data within time window
        time_window_start = sat_row['datetime'] - pd.Timedelta(hours=max_time_hours)
        time_window_end = sat_row['datetime'] + pd.Timedelta(hours=max_time_hours)
        
        era5_in_time = era5_df[
            (era5_df['datetime'] >= time_window_start) &
            (era5_df['datetime'] <= time_window_end)
        ]
        
        if len(era5_in_time) == 0:
            continue
        
        # Calculate distance to all ERA5 points in time window
        distances = haversine_distance(
            sat_row['lat'], sat_row['lon'],
            era5_in_time['lat'].values, era5_in_time['lon'].values
        )
        
        # Find closest ERA5 point
        min_dist_idx = np.argmin(distances)
        min_distance = distances[min_dist_idx]
        
        if min_distance <= max_distance_km:
            era5_match = era5_in_time.iloc[min_dist_idx]
            
            # Calculate time difference in hours
            time_diff = abs((sat_row['datetime'] - era5_match['datetime']).total_seconds() / 3600)
            
            matches.append({
                'datetime_era5': era5_match['datetime'],
                'datetime_sat': sat_row['datetime'],
                'time_diff_hours': time_diff,
                'lat_era5': era5_match['lat'],
                'lon_era5': era5_match['lon'],
                'lat_sat': sat_row['lat'],
                'lon_sat': sat_row['lon'],
                'distance_km': min_distance,
                'swh_era5': era5_match['swh'],
                'swh_sat': sat_row['swh_sat'],
                'satellite': sat_row['satellite']
            })
    
    matches_df = pd.DataFrame(matches)
    
    if len(matches_df) == 0:
        print("❌ No matches found!")
        return matches_df
    
    print(f"\n✅ Found {len(matches_df):,} matched pairs")
    print(f"   Mean distance: {matches_df['distance_km'].mean():.1f} km")
    print(f"   Mean time difference: {matches_df['time_diff_hours'].mean():.2f} hours")
    print(f"   SWH range - ERA5: {matches_df['swh_era5'].min():.2f}-{matches_df['swh_era5'].max():.2f} m")
    print(f"   SWH range - Satellite: {matches_df['swh_sat'].min():.2f}-{matches_df['swh_sat'].max():.2f} m")
    
    return matches_df


def plot_comparison(matches_df, output_file):
    """
    Create scatter plot comparing ERA5 and satellite SWH.
    
    Args:
        matches_df: DataFrame with matched pairs
        output_file: Path to save figure
    """
    print(f"\n📊 Creating comparison plot...")
    
    # Remove any NaN or invalid values
    valid_data = matches_df[
        (matches_df['swh_era5'].notna()) & 
        (matches_df['swh_sat'].notna()) &
        (matches_df['swh_era5'] >= 0) &
        (matches_df['swh_sat'] >= 0)
    ].copy()
    
    # Remove extreme outliers (likely bad data)
    # Keep only values within reasonable range for wave heights
    valid_data = valid_data[
        (valid_data['swh_era5'] < 20) &  # ERA5 max realistic SWH
        (valid_data['swh_sat'] < 20)     # Satellite max realistic SWH
    ]
    
    print(f"   After quality control: {len(valid_data):,} valid pairs")
    
    if len(valid_data) == 0:
        print("❌ No valid data for plotting!")
        return
    
    x = valid_data['swh_sat'].values
    y = valid_data['swh_era5'].values
    
    # Calculate statistics
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    r2 = r_value ** 2
    rmse = np.sqrt(np.mean((y - x) ** 2))
    bias = np.mean(y - x)
    n = len(x)
    
    # Calculate density for color mapping using KDE
    print(f"   Calculating point density with KDE...")
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    
    # Sort points by density (plot low density points first)
    idx = z.argsort()
    x, y, z = x[idx], y[idx], z[idx]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Scatter plot with density coloring (turbo colormap)
    scatter = ax.scatter(x, y, c=z, s=20, cmap='turbo', alpha=0.6, 
                        edgecolors='none', rasterized=True)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label('Point Density (KDE)', fontsize=11, fontweight='bold')
    
    # Plot 1:1 line
    max_val = max(x.max(), y.max())
    min_val = min(x.min(), y.min())
    ax.plot([min_val, max_val], [min_val, max_val], 
            'k--', linewidth=2, label='1:1 Line', alpha=0.7)
    
    # Plot regression line
    x_reg = np.array([min_val, max_val])
    y_reg = slope * x_reg + intercept
    ax.plot(x_reg, y_reg, 'r-', linewidth=2.5, 
            label=f'Regression (y={slope:.3f}x+{intercept:.3f})', alpha=0.8)
    
    # Add statistics text box
    stats_text = f'N = {n:,}\n'
    stats_text += f'R² = {r2:.3f}\n'
    stats_text += f'RMSE = {rmse:.3f} m\n'
    stats_text += f'Bias = {bias:.3f} m\n'
    stats_text += f'Slope = {slope:.3f}\n'
    stats_text += f'Intercept = {intercept:.3f} m'
    
    ax.text(0.05, 0.95, stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=1.5),
            family='monospace')
    
    # Labels and formatting
    ax.set_xlabel('Satellite SWH (m)', fontsize=13, fontweight='bold')
    ax.set_ylabel('ERA5 SWH (m)', fontsize=13, fontweight='bold')
    ax.set_title('ERA5 vs Satellite Significant Wave Height\nAkará Cyclone (All Matches)', 
                fontsize=14, fontweight='bold', pad=15)
        
    # Tick labels
    ax.tick_params(axis='both', labelsize=11)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Legend
    ax.legend(loc='lower right', fontsize=10, frameon=True, 
             fancybox=True, shadow=True, framealpha=0.9)
    
    # Set axis limits with some padding
    pad = 0.5
    ax.set_xlim(x.min() - pad, x.max() + pad)
    ax.set_ylim(y.min() - pad, y.max() + pad)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"💾 Saved: {output_file}")
    plt.close()
    
    # Print summary
    print("\n" + "="*60)
    print("COMPARISON STATISTICS")
    print("="*60)
    print(f"Number of matched pairs: {n:,}")
    print(f"Correlation (R²): {r2:.3f}")
    print(f"Root Mean Square Error: {rmse:.3f} m")
    print(f"Bias (ERA5 - Satellite): {bias:.3f} m")
    print(f"Regression slope: {slope:.3f}")
    print(f"Regression intercept: {intercept:.3f} m")
    print("="*60)


def main():
    """Main function."""
    # Get project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    figures_dir = project_root / 'figures'
    figures_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("ERA5 vs SATELLITE COMPARISON")
    print("="*60)
    
    # Check if matches already exist
    matches_csv = data_dir / 'era5_satellite_matches.csv'
    
    if matches_csv.exists():
        print(f"\n📂 Found existing matches file: {matches_csv.name}")
        print("   Loading pre-computed matches...")
        matches_df = pd.read_csv(matches_csv)
        matches_df['datetime_era5'] = pd.to_datetime(matches_df['datetime_era5'])
        matches_df['datetime_sat'] = pd.to_datetime(matches_df['datetime_sat'])
        print(f"   ✓ Loaded {len(matches_df):,} matched pairs")
    else:
        print("\n📂 No existing matches found. Computing matches...")
        
        # Load ERA5 data
        era5_file = data_dir / 'era5_waves' / 'era5_waves_akara_20240216_20240220.nc'
        if not era5_file.exists():
            # Try to find any ERA5 file in the directory
            era5_files = list((data_dir / 'era5_waves').glob('*.nc'))
            if era5_files:
                era5_file = era5_files[0]
                print(f"ℹ️  Using ERA5 file: {era5_file.name}")
            else:
                print(f"❌ ERA5 file not found in: {data_dir / 'era5_waves'}")
                return
        
        era5_df = load_era5_data(era5_file)
        
        # Load satellite data
        sat_df = load_satellite_data(data_dir)
        
        # Match ERA5 and satellite data
        matches_df = match_era5_satellite(era5_df, sat_df, max_distance_km=50, max_time_hours=1)
        
        if len(matches_df) == 0:
            print("❌ No matches found. Cannot create comparison plot.")
            return
        
        # Save matched data
        matches_df.to_csv(matches_csv, index=False)
        print(f"\n💾 Matched data saved to: {matches_csv}")
    
    # Create comparison plot
    output_fig = figures_dir / 'era5_satellite_comparison.png'
    plot_comparison(matches_df, output_fig)
    
    print("\n✅ Analysis complete!")


if __name__ == '__main__':
    main()
