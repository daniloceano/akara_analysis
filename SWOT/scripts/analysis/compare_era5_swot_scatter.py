#!/usr/bin/env python3
"""
Compare ERA5 x SWOT SWH data using scatter plots with density and statistics
Two approaches:
1) Find nearest ERA5 point for each SWOT observation
2) Interpolate SWOT data to ERA5 grid

Similar to the scatter plot analysis figure provided by the user.

Author: Danilo Couto de Souza
Date: September 2024
Project: SWOT Analysis - Cyclone Akará - Waves Workshop
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from scipy.stats import pearsonr, linregress
from scipy.interpolate import griddata
import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

class ERA5SWOTComparison:
    """Class to compare ERA5 and SWOT SWH data with scatter plots and statistics."""
    
    def __init__(self, swot_dir, era5_file, output_dir):
        """Initialize the comparison analysis."""
        self.swot_dir = Path(swot_dir)
        self.era5_file = era5_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 SWOT Data: {self.swot_dir}")
        print(f"📁 ERA5 File: {self.era5_file}")
        print(f"📊 Analysis Output: {self.output_dir}")
        
        # Geographic limits for consistency
        self.region_extent = [-50, -30, -35, -15]  # [lon_min, lon_max, lat_min, lat_max]
        print(f"🌊 Geographic bounds: {self.region_extent[0]}°W to {self.region_extent[1]}°W, {self.region_extent[2]}°S to {self.region_extent[3]}°S")
        
        # Load data
        self.load_swot_data()
        self.load_era5_data()
    
    def load_swot_data(self):
        """Load and filter SWOT data using the same methodology as snapshots script."""
        print("🎯 Loading SWOT WindWave data...")
        
        # Find all SWOT WindWave files
        swot_files = list(self.swot_dir.glob("SWOT_L2_LR_SSH_WindWave_*.nc"))
        print(f"✅ Found {len(swot_files)} SWOT WindWave files")
        
        if not swot_files:
            raise FileNotFoundError(f"No SWOT files found in {self.swot_dir}")
        
        # Lists to store filtered data
        swot_times_list = []
        swot_lats_list = []
        swot_lons_list = []
        swot_swh_list = []
        
        print("🔍 Applying quality filters...")
        total_points = 0
        filtered_points = 0
        
        for i, file_path in enumerate(swot_files):
            print(f"   Processing file {i+1}/{len(swot_files)}: {file_path.name[:50]}...")
            
            try:
                # Load file
                ds = xr.open_dataset(file_path)
                
                # Get data arrays
                lats = ds.latitude.values
                lons = ds.longitude.values
                swh = ds.swh_karin.values
                surface_flag = ds.ancillary_surface_classification_flag.values
                rain_flag = ds.rain_flag.values
                
                # Convert longitude from 0-360 to -180-180 if needed
                lons = np.where(lons > 180, lons - 360, lons)
                
                # Get time (assume constant for file)
                time_val = pd.to_datetime(ds.time.values[0])
                
                # Flatten arrays for easier processing
                lats_flat = lats.flatten()
                lons_flat = lons.flatten()
                swh_flat = swh.flatten()
                surface_flag_flat = surface_flag.flatten()
                rain_flag_flat = rain_flag.flatten()
                
                total_points += len(lats_flat)
                
                # Apply quality filters
                quality_mask = (
                    (surface_flag_flat == 0) &          # open_ocean only
                    (rain_flag_flat <= 1) &             # no_rain or probable_rain
                    (~np.isnan(swh_flat)) &              # valid SWH
                    (swh_flat >= 0) &                    # positive SWH
                    (swh_flat < 20) &                    # reasonable SWH values
                    (lons_flat >= self.region_extent[0]) &   # region filter
                    (lons_flat <= self.region_extent[1]) &
                    (lats_flat >= self.region_extent[2]) &
                    (lats_flat <= self.region_extent[3])
                )
                
                # Apply mask
                if quality_mask.any():
                    valid_count = quality_mask.sum()
                    filtered_points += valid_count
                    
                    # Store filtered data
                    swot_times_list.extend([time_val] * valid_count)
                    swot_lats_list.extend(lats_flat[quality_mask])
                    swot_lons_list.extend(lons_flat[quality_mask])
                    swot_swh_list.extend(swh_flat[quality_mask])
                    
                    print(f"      ✅ {valid_count:,} valid points")
                else:
                    print(f"      ❌ No valid points")
                
                ds.close()
                
            except Exception as e:
                print(f"      ⚠️ Error processing {file_path.name}: {e}")
                continue
        
        # Create filtered dataset
        if swot_times_list:
            print(f"\n📊 FILTER SUMMARY:")
            print(f"   Total raw points: {total_points:,}")
            print(f"   Points after filters: {filtered_points:,}")
            print(f"   Approval rate: {filtered_points/total_points*100:.1f}%")
            
            # Create xarray dataset
            self.swot_data = xr.Dataset({
                'swh': (['obs'], swot_swh_list),
                'latitude': (['obs'], swot_lats_list),
                'longitude': (['obs'], swot_lons_list),
                'time': (['obs'], swot_times_list)
            })
            
            print(f"✅ SWOT data loaded: {len(self.swot_data.obs):,} filtered oceanic observations")
            
        else:
            raise ValueError("No valid SWOT data found after applying filters")
    
    def load_era5_data(self):
        """Load ERA5 data for comparison."""
        print("🌊 Loading ERA5 SWH data...")
        
        # Load ERA5 data
        era5_raw = xr.open_dataset(self.era5_file)
        
        # Process ERA5 data - average over ensemble members if present
        if 'number' in era5_raw.dims:
            self.era5_data = era5_raw.mean('number')
        else:
            self.era5_data = era5_raw
            
        # Remove expver dimension if present
        if 'expver' in self.era5_data.dims:
            self.era5_data = self.era5_data.isel(expver=0)
            
        print(f"✅ ERA5 SWH: {len(self.era5_data.valid_time)} temporal points")
        print(f"   Spatial resolution: {len(self.era5_data.longitude)} x {len(self.era5_data.latitude)} grid points")
    
    def find_nearest_era5_points(self, time_window_hours=3):
        """
        Find nearest ERA5 grid points for each SWOT observation.
        
        Parameters:
        -----------
        time_window_hours : float
            Time window in hours for temporal matching
        """
        print(f"\n🎯 METHOD 1: Finding nearest ERA5 points (±{time_window_hours}h time window)")
        
        # Create lists for matched data
        swot_matched = []
        era5_matched = []
        
        # Get ERA5 coordinates
        era5_lons = self.era5_data.longitude.values
        era5_lats = self.era5_data.latitude.values
        era5_times = self.era5_data.valid_time.values
        
        # Create coordinate meshgrid for ERA5
        era5_lon_grid, era5_lat_grid = np.meshgrid(era5_lons, era5_lats)
        era5_coords = np.column_stack([era5_lon_grid.ravel(), era5_lat_grid.ravel()])
        
        # Build KDTree for spatial nearest neighbor search
        tree = cKDTree(era5_coords)
        
        print(f"   Processing {len(self.swot_data.obs):,} SWOT observations...")
        
        for i, swot_time in enumerate(self.swot_data.time.values):
            if i % 50000 == 0:
                print(f"   Progress: {i:,}/{len(self.swot_data.obs):,} ({i/len(self.swot_data.obs)*100:.1f}%)")
            
            # Find nearest ERA5 time
            swot_pd_time = pd.to_datetime(swot_time)
            era5_pd_times = pd.to_datetime(era5_times)
            time_diffs = np.abs(era5_pd_times - swot_pd_time)
            
            # Check if within time window
            min_time_diff = time_diffs.min()
            if min_time_diff <= pd.Timedelta(hours=time_window_hours):
                nearest_time_idx = time_diffs.argmin()
                
                # Get SWOT coordinates
                swot_lon = self.swot_data.longitude.isel(obs=i).values
                swot_lat = self.swot_data.latitude.isel(obs=i).values
                swot_swh = self.swot_data.swh.isel(obs=i).values
                
                # Find nearest ERA5 grid point
                _, nearest_idx = tree.query([swot_lon, swot_lat])
                
                # Convert flat index to 2D indices
                lat_idx, lon_idx = np.unravel_index(nearest_idx, (len(era5_lats), len(era5_lons)))
                
                # Get ERA5 SWH value
                era5_swh = self.era5_data.swh.isel(valid_time=nearest_time_idx, latitude=lat_idx, longitude=lon_idx).values
                
                # Check for valid ERA5 data
                if not np.isnan(era5_swh):
                    swot_matched.append(swot_swh)
                    era5_matched.append(era5_swh)
        
        print(f"   ✅ Matched {len(swot_matched):,} observations")
        
        self.swot_nearest = np.array(swot_matched)
        self.era5_nearest = np.array(era5_matched)
        
        return len(swot_matched)
    
    def interpolate_swot_to_era5_grid(self, time_window_hours=3):
        """
        Interpolate SWOT observations to ERA5 grid for each time step.
        
        Parameters:
        -----------
        time_window_hours : float
            Time window in hours for temporal binning
        """
        print(f"\n🎯 METHOD 2: Interpolating SWOT to ERA5 grid (±{time_window_hours}h time window)")
        
        # Get ERA5 grid
        era5_lons = self.era5_data.longitude.values
        era5_lats = self.era5_data.latitude.values
        era5_times = self.era5_data.valid_time.values
        
        # Create target grid
        target_lons, target_lats = np.meshgrid(era5_lons, era5_lats)
        target_points = np.column_stack([target_lons.ravel(), target_lats.ravel()])
        
        # Lists for interpolated comparisons
        swot_interp_list = []
        era5_grid_list = []
        
        print(f"   Processing {len(era5_times)} ERA5 time steps...")
        
        for t, era5_time in enumerate(era5_times):
            if t % 10 == 0:
                print(f"   Time step {t+1}/{len(era5_times)} ({(t+1)/len(era5_times)*100:.1f}%)")
            
            # Find SWOT observations within time window
            era5_pd_time = pd.to_datetime(era5_time)
            swot_times = pd.to_datetime(self.swot_data.time.values)
            time_mask = np.abs(swot_times - era5_pd_time) <= pd.Timedelta(hours=time_window_hours)
            
            if time_mask.sum() > 10:  # Need at least 10 points for interpolation
                # Get SWOT data for this time window
                swot_subset = self.swot_data.isel(obs=time_mask)
                
                # Source points (SWOT coordinates)
                source_points = np.column_stack([
                    swot_subset.longitude.values,
                    swot_subset.latitude.values
                ])
                source_values = swot_subset.swh.values
                
                # Interpolate to ERA5 grid using linear interpolation
                try:
                    interpolated_swh = griddata(
                        source_points, source_values, target_points,
                        method='linear', fill_value=np.nan
                    )
                    
                    # Reshape back to grid
                    interpolated_grid = interpolated_swh.reshape(target_lons.shape)
                    
                    # Get corresponding ERA5 data
                    era5_swh_grid = self.era5_data.swh.isel(valid_time=t).values
                    
                    # Find valid comparisons (both SWOT interpolated and ERA5 have data)
                    valid_mask = ~np.isnan(interpolated_grid) & ~np.isnan(era5_swh_grid)
                    
                    if valid_mask.sum() > 0:
                        swot_interp_list.extend(interpolated_grid[valid_mask])
                        era5_grid_list.extend(era5_swh_grid[valid_mask])
                
                except Exception as e:
                    print(f"      Warning: Interpolation failed for time step {t}: {e}")
                    continue
        
        print(f"   ✅ Interpolated {len(swot_interp_list):,} grid points")
        
        self.swot_interpolated = np.array(swot_interp_list)
        self.era5_gridded = np.array(era5_grid_list)
        
        return len(swot_interp_list)
    
    def calculate_statistics(self, observed, modeled, method_name):
        """Calculate comparison statistics."""
        print(f"\n📊 Statistics for {method_name}:")
        
        # Basic statistics
        n_entries = len(observed)
        obs_mean = np.mean(observed)
        mod_mean = np.mean(modeled)
        obs_std = np.std(observed)
        mod_std = np.std(modeled)
        
        # Bias and RMSE
        bias = np.mean(modeled - observed)
        rmse = np.sqrt(np.mean((modeled - observed)**2))
        
        # Correlation and regression
        r, p_value = pearsonr(observed, modeled)
        slope, intercept, r_value, _, _ = linregress(observed, modeled)
        
        # Scatter Index (SI)
        si = rmse / obs_mean
        
        print(f"   Entries: {n_entries:,}")
        print(f"   μ_obs: {obs_mean:.2f} m | μ_mod: {mod_mean:.2f} m")
        print(f"   σ_obs: {obs_std:.2f} m | σ_mod: {mod_std:.2f} m")
        print(f"   RMSE: {rmse:.2f} m | Bias: {bias:+.2f} m")
        print(f"   SI: {si:.2f} | r: {r:.2f}")
        print(f"   Regression: y = {slope:.2f}x + {intercept:.2f}")
        
        return {
            'n_entries': n_entries,
            'obs_mean': obs_mean, 'mod_mean': mod_mean,
            'obs_std': obs_std, 'mod_std': mod_std,
            'bias': bias, 'rmse': rmse, 'si': si,
            'correlation': r, 'p_value': p_value,
            'slope': slope, 'intercept': intercept,
            'r_squared': r_value**2
        }
    
    def create_comparison_figure(self):
        """Create dual scatter plot comparison figure."""
        print("\n🎨 Creating comparison scatter plots...")
        
        # Calculate statistics for both methods
        stats_nearest = self.calculate_statistics(self.swot_nearest, self.era5_nearest, "Nearest Point Method")
        stats_interp = self.calculate_statistics(self.swot_interpolated, self.era5_gridded, "Grid Interpolation Method")
        
        # Set up the figure (similar to provided image)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        fig.patch.set_facecolor('white')
        
        # Color limits for density plots
        vmin_obs = 0
        vmax_obs = max(np.max(self.swot_nearest), np.max(self.swot_interpolated))
        
        # METHOD 1: Nearest Point
        ax1.hexbin(self.swot_nearest, self.era5_nearest, 
                  gridsize=50, cmap='plasma', mincnt=1,
                  extent=[vmin_obs, vmax_obs, vmin_obs, vmax_obs])
        
        # 1:1 line
        ax1.plot([vmin_obs, vmax_obs], [vmin_obs, vmax_obs], 'b--', linewidth=2, alpha=0.8, label='1:1 line')
        
        # Regression line
        x_reg = np.linspace(vmin_obs, vmax_obs, 100)
        y_reg = stats_nearest['slope'] * x_reg + stats_nearest['intercept']
        ax1.plot(x_reg, y_reg, 'r-', linewidth=2, alpha=0.8, 
                label=f"y = {stats_nearest['slope']:.2f}x + {stats_nearest['intercept']:.2f}")
        
        # Labels and title
        ax1.set_xlabel('SWOT SWH (m)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('ERA5 SWH (m)', fontsize=14, fontweight='bold')
        ax1.set_title('a) ERA5 x SWOT (Nearest Point)', fontsize=16, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        # Statistics text
        stats_text1 = (f"entries = {stats_nearest['n_entries']:,}\n"
                      f"μ_obs = {stats_nearest['obs_mean']:.2f} (m) | μ_mod = {stats_nearest['mod_mean']:.2f} (m)\n"
                      f"σ_obs = {stats_nearest['obs_std']:.2f} (m) | σ_mod = {stats_nearest['mod_std']:.2f} (m)\n"
                      f"rmse = {stats_nearest['rmse']:.2f} (m) | bias = {stats_nearest['bias']:+.2f} (m)\n"
                      f"SI = {stats_nearest['si']:.2f} | r = {stats_nearest['correlation']:.2f}")
        
        ax1.text(0.02, 0.98, stats_text1, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                color='red')
        
        # METHOD 2: Grid Interpolation
        ax2.hexbin(self.swot_interpolated, self.era5_gridded, 
                  gridsize=50, cmap='plasma', mincnt=1,
                  extent=[vmin_obs, vmax_obs, vmin_obs, vmax_obs])
        
        # 1:1 line
        ax2.plot([vmin_obs, vmax_obs], [vmin_obs, vmax_obs], 'b--', linewidth=2, alpha=0.8, label='1:1 line')
        
        # Regression line
        y_reg2 = stats_interp['slope'] * x_reg + stats_interp['intercept']
        ax2.plot(x_reg, y_reg2, 'r-', linewidth=2, alpha=0.8, 
                label=f"y = {stats_interp['slope']:.2f}x + {stats_interp['intercept']:.2f}")
        
        # Labels and title
        ax2.set_xlabel('SWOT SWH (m)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('ERA5 SWH (m)', fontsize=14, fontweight='bold')
        ax2.set_title('b) ERA5 x SWOT (Grid Interpolation)', fontsize=16, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        
        # Statistics text
        stats_text2 = (f"entries = {stats_interp['n_entries']:,}\n"
                      f"μ_obs = {stats_interp['obs_mean']:.2f} (m) | μ_mod = {stats_interp['mod_mean']:.2f} (m)\n"
                      f"σ_obs = {stats_interp['obs_std']:.2f} (m) | σ_mod = {stats_interp['mod_std']:.2f} (m)\n"
                      f"rmse = {stats_interp['rmse']:.2f} (m) | bias = {stats_interp['bias']:+.2f} (m)\n"
                      f"SI = {stats_interp['si']:.2f} | r = {stats_interp['correlation']:.2f}")
        
        ax2.text(0.02, 0.98, stats_text2, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                color='red')
        
        # Set equal aspect and limits
        max_val = max(vmax_obs, np.max(self.era5_nearest), np.max(self.era5_gridded))
        for ax in [ax1, ax2]:
            ax.set_xlim(vmin_obs, max_val)
            ax.set_ylim(vmin_obs, max_val)
            ax.set_aspect('equal')
        
        plt.tight_layout()
        
        # Save figure
        save_path = self.output_dir / "era5_swot_scatter_comparison.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✅ Comparison figure saved: {save_path}")
        
        # Also save as PDF for publications
        save_path_pdf = self.output_dir / "era5_swot_scatter_comparison.pdf"
        plt.savefig(save_path_pdf, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✅ PDF version saved: {save_path_pdf}")
        
        plt.show()
        
        return stats_nearest, stats_interp

def main():
    """Main execution function."""
    print("📊 ERA5 x SWOT SWH SCATTER PLOT COMPARISON")
    print("=" * 60)
    
    # File paths
    swot_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_WINDWAVE_2.0"
    era5_file = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/era5_waves/era5_waves_akara_20240216_20240220.nc"
    output_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/analysis/scatter_comparison"
    
    # Check paths
    if not Path(swot_dir).exists():
        print(f"❌ SWOT directory not found: {swot_dir}")
        return
        
    if not Path(era5_file).exists():
        print(f"❌ ERA5 file not found: {era5_file}")
        return
    
    # Create comparison analyzer
    analyzer = ERA5SWOTComparison(swot_dir, era5_file, output_dir)
    
    # Method 1: Nearest ERA5 points
    n_nearest = analyzer.find_nearest_era5_points(time_window_hours=3)
    
    if n_nearest == 0:
        print("❌ No matching data found for nearest point method!")
        return
    
    # Method 2: SWOT interpolation to ERA5 grid
    n_interp = analyzer.interpolate_swot_to_era5_grid(time_window_hours=3)
    
    if n_interp == 0:
        print("❌ No interpolated data generated!")
        return
    
    # Create comparison figure
    stats_nearest, stats_interp = analyzer.create_comparison_figure()
    
    print("\n✅ COMPARISON ANALYSIS COMPLETED!")
    print(f"📁 Results saved to: {analyzer.output_dir}")
    print("\n📋 SUMMARY:")
    print("✅ Two comparison methods implemented:")
    print("   1) Nearest ERA5 point to each SWOT observation")
    print("   2) SWOT interpolated to ERA5 grid")
    print("✅ Density scatter plots with statistics")
    print("✅ Statistical metrics: bias, RMSE, SI, correlation")
    print("✅ Both PNG and PDF outputs for publication")

if __name__ == "__main__":
    main()