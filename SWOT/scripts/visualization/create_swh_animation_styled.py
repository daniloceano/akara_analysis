#!/usr/bin/env python3
"""
Create professional SWH animation from SWOT WindWave data
Using the existing data loading from snapshots script with SSH animation style
High-quality animation for congress presentations

Author: Danilo Couto de Souza
Date: September 2025
Project: SWOT Analysis - Cyclone Akará - Waves Workshop
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cmocean
from scipy.stats import binned_statistic_2d
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SWOTSWHAnimatorStyled:
    """Class to create SWH animations from SWOT WindWave data with professional style."""
    
    def __init__(self, swot_dir, era5_file, output_dir):
        """Initialize the animator using existing data loading methodology."""
        self.swot_dir = Path(swot_dir)
        self.era5_file = era5_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 SWOT Data: {self.swot_dir}")
        print(f"📁 ERA5 File: {self.era5_file}")
        print(f"🎬 Animations: {self.output_dir}")
        
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
        
        # Create time bins for animation
        self.create_time_bins()
    
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
        Using the same methodology as snapshots script
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
                
                # Apply quality filters (same as snapshots script)
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
            print(f"\\n📊 FILTER SUMMARY:")
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
    
    def create_time_bins(self):
        """Create time bins based on ERA5 temporal grid for animation frames."""
        # Use ERA5 times as the temporal grid
        self.era5_times = self.era5_data.valid_time.values
        
        print(f"📅 Using ERA5 temporal grid: {len(self.era5_times)} timesteps")
        
        # Pre-calculate SWOT data for each ERA5 time
        self.bin_data = []
        swot_times = pd.to_datetime(self.swot_data.time.values)
        
        for i, era5_time in enumerate(self.era5_times):
            era5_pd_time = pd.to_datetime(era5_time)
            
            # Get SWOT data within ±3 hours of ERA5 time
            time_window = pd.Timedelta(hours=3)
            time_mask = np.abs(swot_times - era5_pd_time) <= time_window
            
            # Use isel with mask indices
            mask_indices = np.where(time_mask)[0]
            if len(mask_indices) > 0:
                bin_points = self.swot_data.isel(obs=mask_indices)
            else:
                # Create empty dataset with same structure
                bin_points = xr.Dataset({
                    'swh': (['obs'], []),
                    'latitude': (['obs'], []),
                    'longitude': (['obs'], []),
                    'time': (['obs'], [])
                })
            
            self.bin_data.append(bin_points)
            
            n_points = len(bin_points.obs)
            print(f"   ERA5 {i+1:2d}: {era5_pd_time.strftime('%Y-%m-%d %H:%M')} → {n_points:,} SWOT points")
    
    def create_animation_base(self, figsize=(16, 10)):
        """
        Create base for animation (SSH animation style).
        
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
    
    def create_swh_animation(self, fps=2, duration_seconds=15):
        """
        Create SWH animation with professional style (SSH animation style) using pcolormesh.
        ERA5 data as background, SWOT data overlaid using pcolormesh like SSH animation.
        
        Parameters:
        -----------
        fps : int
            Frames per second
        duration_seconds : int
            Total duration in seconds
        """
        if self.swot_data is None:
            print("❌ SWOT data not loaded!")
            return None
        
        print(f"🎬 Creating SWH animation with ERA5 background and SWOT pcolormesh overlay...")
        
        # Calculate number of frames
        total_frames = fps * duration_seconds
        n_era5_times = len(self.era5_times)
        
        # Select time indices for animation
        if total_frames >= n_era5_times:
            # Use all available ERA5 timesteps
            time_indices = list(range(n_era5_times))
        else:
            # Sample evenly across available ERA5 timesteps
            time_indices = np.linspace(0, n_era5_times-1, total_frames, dtype=int)
        
        print(f"🎞️ {len(time_indices)} frames, {fps} FPS")
        
        # Create figure base
        fig, ax = self.create_animation_base()
        
        # Color scale (plasma colormap like current SWH visualizations)
        cmap = plt.cm.plasma
        
        # Prepare grid for SWOT data binning (like SSH animation)
        # But we'll use scatter plot for SWOT to avoid grid issues
        
        # Initial plots - ERA5 background
        era5_lons, era5_lats = np.meshgrid(self.era5_data.longitude, self.era5_data.latitude)
        era5_swh_init = self.era5_data.swh.isel(valid_time=time_indices[0])
        
        # ERA5 background plot (bottom layer)
        im_era5 = ax.pcolormesh(
            era5_lons, era5_lats, era5_swh_init,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            shading='auto',
            alpha=0.6
        )
        
        # SWOT scatter overlay (top layer) - initially empty
        scat_swot = ax.scatter([], [], c=[], s=25, cmap=cmap, vmin=self.vmin, vmax=self.vmax, 
                              transform=ccrs.PlateCarree(), alpha=1.0)
        
        # Colorbar (SSH style)
        cbar = plt.colorbar(
            scat_swot, ax=ax, 
            orientation='horizontal', 
            pad=0.05, 
            shrink=0.7,
            aspect=25
        )
        cbar.set_label('Significant Wave Height (m)', fontsize=16, color='white', weight='bold')
        cbar.ax.tick_params(labelsize=14, colors='white')
        cbar.outline.set_edgecolor('white')
        
        # Dynamic title (SSH style)
        title = ax.set_title('', fontsize=20, color='white', weight='bold', pad=20)
        
        # Info text (SSH style)
        info_text = ax.text(
            0.02, 0.98, '', transform=ax.transAxes,
            fontsize=12, color='white', weight='bold',
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
        )
        
        # Frame counter (SSH style)
        frame_text = ax.text(
            0.98, 0.98, '', transform=ax.transAxes,
            fontsize=10, color='yellow', weight='bold',
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7)
        )
        
        def animate(frame):
            """Animation function."""
            if frame >= len(time_indices):
                return im_era5, scat_swot, title, info_text, frame_text
            
            time_idx = time_indices[frame]
            era5_time = self.era5_times[time_idx]
            era5_pd_time = pd.to_datetime(era5_time)
            
            # Update ERA5 background
            era5_swh = self.era5_data.swh.isel(valid_time=time_idx)
            im_era5.set_array(era5_swh.values.ravel())
            
            # Get SWOT data for this time
            bin_data = self.bin_data[time_idx]
            n_points = len(bin_data.obs)
            
            if n_points > 0:
                # Update scatter plot with SWOT data
                lons = bin_data.longitude.values
                lats = bin_data.latitude.values
                swh_vals = bin_data.swh.values
                
                # Clear previous data
                scat_swot.set_offsets(np.empty((0, 2)))
                
                # Set new data
                scat_swot.set_offsets(np.column_stack([lons, lats]))
                scat_swot.set_array(swh_vals)
            else:
                # No SWOT data for this time
                scat_swot.set_offsets(np.empty((0, 2)))
                scat_swot.set_array(np.array([]))
            
            # Update title (SWH specific)
            # title.set_text(f'SWOT Significant Wave Height\nTimestep {frame+1}\nCyclone Akará Period')
            
            # Update info text (SSH style)
            time_str = era5_pd_time.strftime('%Y-%m-%d %H:%M')
            info_text.set_text(f'Frame: {frame+1}/{len(time_indices)}\nDay: {time_str}\nData: ERA5 + SWOT SWH')
            
            # Update frame counter
            frame_text.set_text(f'{frame+1}/{len(time_indices)}')
            
            return im_era5, scat_swot, title, info_text, frame_text
        
        # Create animation
        print("🎬 Generating animation...")
        anim = animation.FuncAnimation(
            fig, animate, 
            frames=len(time_indices),
            interval=1000/fps,  # milliseconds between frames
            blit=False,
            repeat=True
        )
        
        # Save animation
        output_file = self.output_dir / "swot_swh_animation_styled.gif"
        print(f"💾 Saving animation: {output_file}")
        
        # Use PillowWriter for better GIF quality
        writer = animation.PillowWriter(fps=fps)
        anim.save(output_file, writer=writer, dpi=150)
        
        print(f"✅ Animation saved: {output_file}")
        print(f"📊 Animation details:")
        print(f"   • Frames: {len(time_indices)}")
        print(f"   • Duration: {len(time_indices)/fps:.1f} seconds")
        print(f"   • FPS: {fps}")
        print(f"   • Geographic bounds: {self.region_extent}")
        print(f"   • Color scale: {self.vmin} - {self.vmax} m")
        print(f"   • ERA5 background + SWOT pcolormesh overlay")
        print(f"   • Total SWOT points: {len(self.swot_data.obs):,}")
        
        plt.close(fig)
        return anim

def main():
    """Main execution function."""
    print("🌊 CREATING SWOT SWH ANIMATION (SSH STYLE + ERA5 BACKGROUND)")
    print("=" * 70)
    
    # File paths
    swot_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_WINDWAVE_2.0"
    era5_file = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/era5_waves/era5_waves_akara_20240216_20240220.nc"
    output_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/figures/swh_animation_styled"
    
    # Check paths
    if not Path(swot_dir).exists():
        print(f"❌ SWOT directory not found: {swot_dir}")
        return
        
    if not Path(era5_file).exists():
        print(f"❌ ERA5 file not found: {era5_file}")
        return
    
    # Create animator
    animator = SWOTSWHAnimatorStyled(swot_dir, era5_file, output_dir)
    
    if animator.swot_data is None:
        print("❌ No data available for animation!")
        return
    
    # Create animation
    anim = animator.create_swh_animation(fps=2, duration_seconds=15)
    
    if anim:
        print("\n✅ SWH ANIMATION COMPLETED!")
        print(f"📁 Output folder: {animator.output_dir}")
        print("\n📋 SUMMARY:")
        print("✅ Professional SSH animation style with ERA5 background")
        print("✅ ERA5 SWH as background field (pcolormesh, alpha=0.6)")
        print("✅ SWOT data overlaid using pcolormesh (alpha=1.0)")
        print("✅ Dark background with gold coastlines")
        print("✅ Filtered oceanic data only (open_ocean + no_rain)")
        print("✅ Geographic bounds: 35°S to 15°S, 50°W to 30°W")
        print("✅ Color scale: 0.0 - 5.9 m (plasma colormap)")
    else:
        print("❌ Animation creation failed!")

if __name__ == "__main__":
    main()