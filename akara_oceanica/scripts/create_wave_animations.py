#!/usr/bin/env python3
"""
Create professional wave height animations combining:
- ERA5 fields (background, hourly gridded data)
- Satellite altimetry data (overlay, minute-level data)

Generates two versions:
1. Animation per individual satellite
2. Animation with all satellites combined

Author: GitHub Copilot + Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
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
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import logging

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# If imageio-ffmpeg is installed in the venv, prefer its bundled ffmpeg binary
try:
    import imageio_ffmpeg
    ffmpeg_path = None
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_path = None

    if ffmpeg_path:
        import matplotlib as mpl
        mpl.rcParams['animation.ffmpeg_path'] = ffmpeg_path
        logger.info(f"🎛️ Using ffmpeg from imageio-ffmpeg: {ffmpeg_path}")
    else:
        logger.info("ℹ️ imageio-ffmpeg present but could not get ffmpeg exe; system ffmpeg may still be required.")
except Exception:
    logger.info("ℹ️ imageio-ffmpeg not installed; system ffmpeg required for saving animations.")

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SatelliteWaveAnimator:
    """Class to create wave animations with ERA5 + satellites."""
    
    def __init__(self, data_dir, era5_file, output_dir, region=None):
        """
        Initialize the animator.
        
        Args:
            data_dir: Directory with satellite data (CSV)
            era5_file: ERA5 NetCDF file
            output_dir: Directory to save animations
            region: Dictionary with bounds {west, east, south, north}
        """
        self.data_dir = PROJECT_ROOT / data_dir
        self.era5_file = PROJECT_ROOT / era5_file
        self.output_dir = PROJECT_ROOT / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default region (Akará)
        if region is None:
            self.region = {
                'west': -50.0,
                'east': -20.0,
                'south': -45.0,
                'north': -15.0
            }
        else:
            self.region = region
        
        logger.info(f"📁 Satellite data: {self.data_dir}")
        logger.info(f"📁 ERA5 data: {self.era5_file}")
        logger.info(f"🎬 Animations: {self.output_dir}")
        logger.info(f"🌍 Region: {self.region}")
        
        # Cores para cada satélite
        self.satellite_colors = {
            'CFOSAT': '#00FFFF',
            'CryoSat-2': '#FF1493',
            'HaiYang-2B': '#FFD700',
            'HaiYang-2C': '#FF8C00',
            'Jason-3': '#00FF00',
            'Saral/AltiKa': '#FF0000',
            'Sentinel-3A': '#FFFF00',
            'Sentinel-3B': '#00CED1',
            'Sentinel-6A': '#9370DB',
            'SWOT_nadir': '#FF69B4',
        }
        
        # Configure style
        self.setup_plotting_style()
        
        # Load data
        self.load_era5_data()
        self.load_satellite_data()
        self.create_time_bins()
    
    def setup_plotting_style(self):
        """Configure professional dark style."""
        plt.style.use('dark_background')
        plt.rcParams.update({
            'font.size': 12,
            'font.family': 'sans-serif',
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 10,
            'figure.titlesize': 18,
            'axes.linewidth': 1.5,
            'grid.linewidth': 0.8,
            'lines.linewidth': 2,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.facecolor': 'black',
            'axes.facecolor': 'black',
            'figure.facecolor': 'black'
        })
    
    def load_era5_data(self):
        """Load ERA5 data."""
        logger.info("🌊 Loading ERA5 data...")
        
        try:
            self.era5_ds = xr.open_dataset(self.era5_file)
            
            # Detect time variable
            if 'valid_time' in self.era5_ds.dims:
                self.era5_ds = self.era5_ds.rename({'valid_time': 'time'})
            
            # Crop to region of interest
            self.era5_ds = self.era5_ds.sel(
                latitude=slice(self.region['north'], self.region['south']),
                longitude=slice(self.region['west'], self.region['east'])
            )
            
            # Detect wave height variable
            if 'swh' in self.era5_ds.variables:
                self.era5_wave_var = 'swh'
            elif 'significant_height_of_combined_wind_waves_and_swell' in self.era5_ds.variables:
                self.era5_wave_var = 'significant_height_of_combined_wind_waves_and_swell'
            else:
                logger.warning("⚠️ Wave height variable not found in ERA5")
                self.era5_wave_var = None
            
            logger.info(f"✅ ERA5 loaded: {len(self.era5_ds.time)} timesteps")
            logger.info(f"📊 Wave variable: {self.era5_wave_var}")
            
        except Exception as e:
            logger.error(f"❌ Error loading ERA5: {e}")
            raise
    
    def load_satellite_data(self):
        """Load data from all satellites."""
        logger.info("🛰️ Loading satellite data...")
        
        self.satellite_data = {}
        satellites = [
            'CFOSAT', 'CryoSat-2', 'HaiYang-2B', 'HaiYang-2C', 'Jason-3',
            'Saral_AltiKa', 'Sentinel-3A', 'Sentinel-3B', 'Sentinel-6A', 'SWOT_nadir'
        ]
        
        for sat in satellites:
            sat_dir = self.data_dir / sat
            
            if not sat_dir.exists():
                logger.warning(f"⚠️ Directory not found: {sat}")
                continue
            
            csv_files = list(sat_dir.glob('*.csv'))
            
            if not csv_files:
                logger.warning(f"⚠️ No CSV data for {sat}")
                continue
            
            try:
                df = pd.read_csv(csv_files[0])
                # Parse times as UTC-aware timestamps to avoid tz-naive vs tz-aware
                # comparison errors when matching with ERA5 time bins.
                df['time'] = pd.to_datetime(df['time'], utc=True)
                
                # Filter only VAVH
                df_vavh = df[df['variable'] == 'VAVH'].copy()
                
                if len(df_vavh) > 0:
                    # Friendly name (remove underscore from Saral)
                    sat_name = sat.replace('_', '/')
                    self.satellite_data[sat_name] = df_vavh
                    logger.info(f"✅ {sat_name}: {len(df_vavh)} points")
                
            except Exception as e:
                logger.error(f"❌ Error loading {sat}: {e}")
        
        logger.info(f"📊 Total: {len(self.satellite_data)} satellites loaded")
    
    def create_time_bins(self):
        """Create hourly time bins to combine ERA5 and satellites."""
        logger.info("⏰ Creating time bins...")
        
        # Get ERA5 time range and ensure UTC timezone
        self.time_bins = pd.to_datetime(self.era5_ds.time.values)
        try:
            # If tz-naive, localize; if already tz-aware, convert to UTC
            if self.time_bins.tz is None:
                self.time_bins = self.time_bins.tz_localize('UTC')
            else:
                self.time_bins = self.time_bins.tz_convert('UTC')
        except Exception:
            # Fallback: force-localize each element if needed
            self.time_bins = pd.DatetimeIndex([pd.to_datetime(t).tz_localize('UTC') if pd.to_datetime(t).tzinfo is None else pd.to_datetime(t).tz_convert('UTC') for t in self.time_bins])

        logger.info(f"📅 Period: {self.time_bins[0]} to {self.time_bins[-1]}")
        logger.info(f"⏱️ Total frames: {len(self.time_bins)}")
    
    def get_satellite_data_for_time(self, time_center, satellite=None):
        """
        Get satellite data for a time window.
        
        Args:
            time_center: Central timestamp (ERA5 hour)
            satellite: Satellite name (None = all)
            
        Returns:
            DataFrame with filtered data
        """
        # Window of ±30 minutes
        time_start = time_center - pd.Timedelta(minutes=30)
        time_end = time_center + pd.Timedelta(minutes=30)
        
        if satellite:
            # Specific satellite
            if satellite in self.satellite_data:
                df = self.satellite_data[satellite]
                mask = (df['time'] >= time_start) & (df['time'] <= time_end)
                return df[mask]
            else:
                return pd.DataFrame()
        else:
            # All satellites
            all_data = []
            for sat_name, df in self.satellite_data.items():
                mask = (df['time'] >= time_start) & (df['time'] <= time_end)
                df_filtered = df[mask].copy()
                df_filtered['satellite'] = sat_name
                all_data.append(df_filtered)
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            else:
                return pd.DataFrame()
    
    def create_single_frame(self, ax, cbar_ax, time_idx, satellite=None):
        """
        Create a single animation frame.
        
        Args:
            ax: Matplotlib axis
            cbar_ax: Colorbar axis
            time_idx: Time index
            satellite: Satellite name (None = all)
        """
        ax.clear()
        
        # Get current time
        current_time = self.time_bins[time_idx]
        
        # Plot ERA5 background field
        im = None
        if self.era5_wave_var:
            era5_data = self.era5_ds[self.era5_wave_var].isel(time=time_idx)
            
            # ERA5 contourf
            im = ax.contourf(
                self.era5_ds.longitude,
                self.era5_ds.latitude,
                era5_data,
                levels=20,
                cmap='turbo',
                vmin=0,
                vmax=8,
                transform=ccrs.PlateCarree(),
                alpha=0.8,
                zorder=1
            )
        
        # Add geographic features
        ax.add_feature(cfeature.LAND, facecolor='#2d2d2d', edgecolor='white', 
                      linewidth=0.5, zorder=2)
        ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='white', zorder=3)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', 
                      edgecolor='gray', alpha=0.5, zorder=2)
        
        # Plot satellite data
        sat_data = self.get_satellite_data_for_time(current_time, satellite)
        
        if len(sat_data) > 0:
            if satellite:
                # Single satellite - color by wave height
                scatter = ax.scatter(
                    sat_data['longitude'],
                    sat_data['latitude'],
                    c=sat_data['value'],
                    s=50,
                    cmap='turbo',
                    vmin=0,
                    vmax=8,
                    linewidth=0.5,
                    transform=ccrs.PlateCarree(),
                    zorder=5,
                    alpha=0.9
                )
            else:
                # Multiple satellites - color by wave height (not by satellite)
                scatter = ax.scatter(
                    sat_data['longitude'],
                    sat_data['latitude'],
                    c=sat_data['value'],
                    s=40,
                    cmap='turbo',
                    vmin=0,
                    vmax=8,
                    linewidth=0.5,
                    transform=ccrs.PlateCarree(),
                    zorder=5,
                    alpha=0.9
                )
        
        # Configure extent
        ax.set_extent([
            self.region['west'],
            self.region['east'],
            self.region['south'],
            self.region['north']
        ], crs=ccrs.PlateCarree())
        
        # Grid
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                         alpha=0.5, linestyle='--', zorder=4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 10, 'color': 'white'}
        gl.ylabel_style = {'size': 10, 'color': 'white'}
        
        # Title
        title_sat = satellite if satellite else "All Satellites"
        ax.set_title(
            f'Wave Height - {title_sat}\n{current_time.strftime("%Y-%m-%d %H:%M UTC")}',
            fontsize=14,
            fontweight='bold',
            color='white',
            pad=10
        )
        
        # Update colorbar
        if im is not None:
            cbar_ax.clear()
            cbar = plt.colorbar(im, cax=cbar_ax, orientation='vertical')
            cbar.set_label('Significant Wave Height (m)', fontsize=12, color='white')
            cbar.ax.tick_params(labelsize=10, colors='white')
        
        return ax
    
    def create_animation(self, satellite=None, fps=2, interval=500):
        """
        Create complete animation.
        
        Args:
            satellite: Satellite name (None = all)
            fps: Frames per second
            interval: Interval between frames (ms)
        """
        sat_name = satellite if satellite else "all_satellites"
        # Make a filesystem-safe name for the output file (no slashes or special dirs)
        file_safe_name = str(sat_name).replace('/', '_')
        logger.info(f"🎬 Creating animation: {sat_name}")
        
        # Create figure with colorbar
        fig = plt.figure(figsize=(18, 10), facecolor='black')
        
        # Create gridspec for main plot and colorbar
        import matplotlib.gridspec as gridspec
        gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1], wspace=0.02)
        
        ax = plt.subplot(gs[0], projection=ccrs.PlateCarree())
        cbar_ax = plt.subplot(gs[1])
        
        # Create animation
        def update_frame(frame_idx):
            logger.info(f"  Frame {frame_idx+1}/{len(self.time_bins)}")
            return self.create_single_frame(ax, cbar_ax, frame_idx, satellite)
        
        anim = animation.FuncAnimation(
            fig,
            update_frame,
            frames=len(self.time_bins),
            interval=interval,
            blit=False,
            repeat=True
        )
        
        # Save
        output_file = self.output_dir / f'wave_animation_{file_safe_name}.mp4'

        logger.info(f"💾 Saving animation: {output_file}")
        writer = animation.FFMpegWriter(fps=fps, bitrate=2000, 
                                       codec='libx264',
                                       extra_args=['-pix_fmt', 'yuv420p'])
        
        anim.save(output_file, writer=writer)
        plt.close(fig)
        
        logger.info(f"✅ Animation saved: {output_file}")
        
        return output_file


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("🎬 ANIMATION CREATION - ERA5 + SATELLITES 🌊")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure paths
    data_dir = 'data'
    era5_file = 'data/era5_waves/era5_waves_akara_20240214_20240222.nc'
    output_dir = 'figures/animations'
    
    # Check if ERA5 exists
    era5_path = PROJECT_ROOT / era5_file
    if not era5_path.exists():
        logger.error(f"❌ ERA5 file not found: {era5_path}")
        logger.info("💡 Run first: python scripts/download_era5_waves.py")
        return
    
    # Create animator
    animator = SatelliteWaveAnimator(data_dir, era5_file, output_dir)
    
    # Option 1: Create animation with all satellites
    logger.info("")
    logger.info("🎯 Option 1: Animation with ALL satellites")
    animator.create_animation(satellite=None, fps=2, interval=500)
    
    # Option 2: Create individual animations
    logger.info("")
    logger.info("🎯 Option 2: Individual animations per satellite")
    
    for satellite in animator.satellite_data.keys():
        logger.info(f"")
        animator.create_animation(satellite=satellite, fps=2, interval=500)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 ANIMATIONS COMPLETE! 🚀")
    logger.info("=" * 60)
    logger.info(f"📁 Saved in: {animator.output_dir}")
    logger.info("")
    logger.info("💡 Next steps:")
    logger.info("   - Open .mp4 files to visualize")
    logger.info("   - Adjust fps/interval if necessary")
    logger.info("   - Use ffmpeg to combine or edit")


if __name__ == "__main__":
    main()
