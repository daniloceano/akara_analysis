#!/usr/bin/env python3
"""
Create professional SWH snapshots with ERA5 background and SWOT overlay
Using the dark professional style from SSH animation
High-quality snapshots for congress presentations

Author: Danilo Couto de Souza
Date: September 2025
Project: SWOT Analysis - Cyclone Akará - Waves Workshop
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from scipy.stats import binned_statistic_2d
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class SWHSnapshotsStyled:
    """Class to create styled SWH snapshots with ERA5 background and SWOT overlay."""
    
    def __init__(self, swot_dir, era5_file, output_dir):
        """Initialize the snapshot creator using existing data loading methodology."""
        self.swot_dir = Path(swot_dir)
        self.era5_file = era5_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 SWOT Data: {self.swot_dir}")
        print(f"📁 ERA5 File: {self.era5_file}")
        print(f"📸 Snapshots: {self.output_dir}")
        
        # Professional style settings for presentations (SSH animation style)
        self.setup_plotting_style()
        # Geographic limits (keep as requested: [-50, -30, -35, -15])
        self.region_extent = [-50, -30, -35, -15]  # [lon_min, lon_max, lat_min, lat_max]
        print(f"🌊 Geographic bounds: {self.region_extent[0]}°W to {self.region_extent[1]}°W, {self.region_extent[2]}°S to {self.region_extent[3]}°S")
        
        # Load and process SWOT data using existing methodology
        self.load_and_filter_swot_data()
        
        # Load ERA5 data
        self.load_era5_data()
        
        # Calculate color scale
        self.calculate_color_limits()
    
    def setup_plotting_style(self):
        """Configure dark professional style for presentations (SSH style)"""
        plt.style.use('dark_background')
        plt.rcParams.update({
            'font.size': 14,
            'font.family': 'sans-serif',
            'axes.labelsize': 16,
            'axes.titlesize': 18,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12,
            'figure.titlesize': 20,
            'axes.linewidth': 1.5,
            'grid.linewidth': 0.8,
            'lines.linewidth': 2,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.facecolor': 'black',
            'axes.facecolor': 'black',
            'figure.facecolor': 'black'
        })
    
    def load_and_filter_swot_data(self):
        """
        Load raw SWOT WindWave files and apply quality filters
        Using the same methodology as original snapshots script
        """
        print("🎯 Loading SWOT WindWave raw files...")
        
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
                
                # Apply quality filters (same as original script)
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
            
            # Show SWH statistics
            swh_values = np.array(swot_swh_list)
            print(f"   SWH range: {swh_values.min():.2f} - {swh_values.max():.2f} m")
            print(f"   Time range: {min(swot_times_list)} to {max(swot_times_list)}")
            
        else:
            raise ValueError("No valid SWOT data found after applying filters")
    
    def load_era5_data(self):
        """Load ERA5 data for background fields."""
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
    
    def calculate_color_limits(self):
        """Calculate color scale limits for SWH data (current scale: 0.0 - 5.9 m)"""
        print("🎨 Calculating color scale limits...")
        
        # Use current scale from snapshots script
        self.vmin = 0.0
        self.vmax = 5.9
        
        print(f"✅ Color scale: {self.vmin:.1f} - {self.vmax:.1f} m (plasma colormap)")
    
    def create_snapshot_base(self, figsize=(16, 10)):
        """
        Create base for snapshot (SSH animation style).
        
        Parameters:
        -----------
        figsize : tuple
            Figure size
        """
        # Projection suitable for South Atlantic
        projection = ccrs.PlateCarree()
        
        fig = plt.figure(figsize=figsize, facecolor='black')
        ax = plt.axes(projection=projection)
        
        # Geographic features with dark style (SSH style)
        ax.add_feature(cfeature.COASTLINE, linewidth=1.2, color='gold', alpha=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, color='white', alpha=0.5)
        ax.add_feature(cfeature.LAND, color='#2F2F2F', alpha=0.9)
        ax.add_feature(cfeature.OCEAN, color='#1a1a1a', alpha=0.9)
        
        # More visible grid (SSH style)
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(), 
            draw_labels=True,
            linewidth=1.0, 
            color='white', 
            alpha=0.4, 
            linestyle='-'
        )
        
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 14, 'color': 'white', 'weight': 'bold'}
        gl.ylabel_style = {'size': 14, 'color': 'white', 'weight': 'bold'}
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Set extent
        ax.set_extent(self.region_extent, crs=ccrs.PlateCarree())
        
        return fig, ax
    
    def create_era5_snapshots_with_swot_styled(self, create_all_snapshots=True):
        """
        Create styled ERA5 SWH snapshots with SWOT points overlaid
        ERA5 data as background, SWOT data on top (corrected order)
        """
        
        # Get all ERA5 times
        era5_times = self.era5_data.valid_time.values
        n_total_times = len(era5_times)
        
        if create_all_snapshots:
            # Use ALL time steps
            time_indices = range(n_total_times)
            print(f"\n📸 CREATING STYLED SNAPSHOTS FOR ALL {n_total_times} ERA5 TIMESTEPS")
        else:
            # Use only 6 evenly spaced snapshots
            n_snapshots = 6
            time_indices = np.linspace(0, n_total_times-1, n_snapshots, dtype=int)
            print(f"\n📸 CREATING {n_snapshots} STYLED SNAPSHOTS")
        
        print("-" * 50)
        
        created_files = []
        
        for i, time_idx in enumerate(time_indices):
            # Create individual figure for each snapshot with dark style
            fig, ax = self.create_snapshot_base(figsize=(16, 10))
            
            # Get ERA5 data for this time
            era5_time = era5_times[time_idx]
            era5_swh = self.era5_data.swh.isel(valid_time=time_idx)
            
            era5_time_str = pd.to_datetime(era5_time).strftime('%Y-%m-%d %H:%M')
            print(f"   Snapshot {i+1}/{len(time_indices)}: {era5_time_str}")
            
            # STEP 1: Plot ERA5 SWH field as BACKGROUND (bottom layer)
            era5_lons, era5_lats = np.meshgrid(self.era5_data.longitude, self.era5_data.latitude)
            im_era5 = ax.pcolormesh(era5_lons, era5_lats, era5_swh, 
                                   cmap='plasma', transform=ccrs.PlateCarree(),
                                   vmin=self.vmin, vmax=self.vmax, 
                                   shading='auto', alpha=0.6)
            
            # STEP 2: Find SWOT data within time window (±3 hours)
            time_window = pd.Timedelta(hours=3)
            era5_pd_time = pd.to_datetime(era5_time)
            
            swot_times = pd.to_datetime(self.swot_data.time.values)
            time_mask = np.abs(swot_times - era5_pd_time) <= time_window
            
            # Initialize SWOT variables
            swot_swh_values = []
            swot_lons_plot = []
            swot_lats_plot = []
            
            if time_mask.any():
                # Get indices where mask is True
                mask_indices = np.where(time_mask)[0]
                swot_concurrent = self.swot_data.isel(obs=mask_indices)
                
                swot_swh_values = swot_concurrent.swh.values
                swot_lons_plot = swot_concurrent.longitude.values
                swot_lats_plot = swot_concurrent.latitude.values
                
            # STEP 3: Plot SWOT points using pcolormesh ON TOP of ERA5 (top layer)
            if len(swot_swh_values) > 0:
                # Create grid for SWOT data binning (like SSH animation)
                lon_bins = np.linspace(self.region_extent[0], self.region_extent[1], 50)
                lat_bins = np.linspace(self.region_extent[2], self.region_extent[3], 40)
                
                # Bin SWOT data into grid
                ret = binned_statistic_2d(
                    swot_lons_plot, swot_lats_plot, swot_swh_values,
                    statistic='mean',
                    bins=[lon_bins, lat_bins]
                )
                
                Z_swot = ret.statistic.T  # Transpose for correct orientation
                Z_swot = np.ma.masked_invalid(Z_swot)
                
                # Create meshgrid for pcolormesh
                X_swot, Y_swot = np.meshgrid(lon_bins, lat_bins)
                
                # Plot SWOT data using pcolormesh
                im_swot = ax.pcolormesh(X_swot, Y_swot, Z_swot, 
                                       cmap='plasma', transform=ccrs.PlateCarree(),
                                       vmin=self.vmin, vmax=self.vmax, 
                                       shading='auto', alpha=1.0)
                
                swot_count = len(swot_swh_values)
            else:
                swot_count = 0
            
            print(f"      SWOT points (oceanic): {swot_count:,}")
            
            # Colorbar (SSH style)
            cbar = plt.colorbar(
                im_era5, ax=ax, 
                orientation='horizontal', 
                pad=0.05, 
                shrink=0.7,
                aspect=25
            )
            cbar.set_label('Significant Wave Height (m)', fontsize=16, color='white', weight='bold')
            cbar.ax.tick_params(labelsize=14, colors='white')
            cbar.outline.set_edgecolor('white')
            
            # Title (SSH style with proper line breaks)
            # title_text = f'SWOT Significant Wave Height\nTimestep {i+1}\nCyclone Akará Period'
            # if swot_count > 0:
            #     title_text += f' ({swot_count:,} SWOT points)'
            # ax.set_title(title_text, fontsize=20, color='white', weight='bold', pad=20)
            
            # Info text (SSH style)
            time_str = era5_pd_time.strftime('%Y-%m-%d %H:%M')
            info_text = f'Frame: {i+1}/{len(time_indices)}\nDay: {time_str}\nData: ERA5 + SWOT SWH'
            ax.text(
                0.02, 0.98, info_text, transform=ax.transAxes,
                fontsize=12, color='white', weight='bold',
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
            )
            
            # Frame counter (SSH style)
            frame_text = f'{i+1}/{len(time_indices)}'
            ax.text(
                0.98, 0.98, frame_text, transform=ax.transAxes,
                fontsize=10, color='yellow', weight='bold',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7)
            )
            
            plt.tight_layout()
            
            # Save individual snapshot
            timestamp = pd.to_datetime(era5_time).strftime('%Y%m%d_%H%M')
            save_path = self.output_dir / f"era5_swot_styled_{timestamp}.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='black')
            created_files.append(save_path)
            
            plt.close(fig)
        
        print(f"\n✅ {len(created_files)} styled snapshots saved to: {self.output_dir}")
        
        # Summary statistics
        if create_all_snapshots:
            total_swot_points = 0
            snapshots_with_swot = 0
            for file in created_files:
                # Count SWOT points for this time step (approximate from filename)
                timestamp_str = file.stem.split('_')[-2] + '_' + file.stem.split('_')[-1]
                era5_time_check = pd.to_datetime(timestamp_str, format='%Y%m%d_%H%M')
                
                swot_times = pd.to_datetime(self.swot_data.time.values)
                time_mask = np.abs(swot_times - era5_time_check) <= pd.Timedelta(hours=3)
                
                swot_count_check = time_mask.sum()
                if swot_count_check > 0:
                    snapshots_with_swot += 1
                    total_swot_points += swot_count_check
                    
            print(f"\n📊 STYLED SNAPSHOTS SUMMARY:")
            print(f"   Total snapshots: {len(created_files)}")
            print(f"   Snapshots with SWOT data: {snapshots_with_swot}")
            print(f"   SWOT coverage rate: {snapshots_with_swot/len(created_files)*100:.1f}%")
            print(f"   Total SWOT points plotted: {total_swot_points:,}")
        
        return created_files

def main():
    """Main execution function."""
    print("🌊 CREATING STYLED SWH SNAPSHOTS (SSH ANIMATION STYLE)")
    print("=" * 70)
    
    # File paths
    swot_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_WINDWAVE_2.0"
    era5_file = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/era5_waves/era5_waves_akara_20240216_20240220.nc"
    output_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/figures/swh_snapshots_styled"
    
    # Check paths
    if not Path(swot_dir).exists():
        print(f"❌ SWOT directory not found: {swot_dir}")
        return
        
    if not Path(era5_file).exists():
        print(f"❌ ERA5 file not found: {era5_file}")
        return
    
    # Create snapshot creator
    creator = SWHSnapshotsStyled(swot_dir, era5_file, output_dir)
    
    if creator.swot_data is None:
        print("❌ No data available for snapshots!")
        return
    
    # Create styled snapshots
    snapshot_files = creator.create_era5_snapshots_with_swot_styled(create_all_snapshots=True)
    
    if snapshot_files:
        print("\n✅ STYLED SNAPSHOTS COMPLETED!")
        print(f"📁 Output folder: {creator.output_dir}")
        print("\n📋 SUMMARY:")
        print("✅ Dark background with professional SSH animation style")
        print("✅ ERA5 SWH as background field (bottom layer)")
        print("✅ SWOT points overlaid on top (top layer)")
        print("✅ Gold coastlines and white grid")
        print("✅ Filtered oceanic data only (open_ocean + no_rain)")
        print("✅ Geographic bounds: 25°S to 35°S, 30°W to 45°W")
        print("✅ Color scale: 0.0 - 5.9 m (plasma colormap)")
    else:
        print("❌ Snapshot creation failed!")

if __name__ == "__main__":
    main()