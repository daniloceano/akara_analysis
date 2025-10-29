#!/usr/bin/env python3
"""
Plot daily mean wave height fields from ERA5 data.

Creates a single figure with subplots (2x5 or similar) showing the daily mean
significant wave height for each day in the dataset.

Author: GitHub Copilot + Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from datetime import datetime
import warnings
import logging

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ERA5DailyMeanPlotter:
    """Plot daily mean wave height fields from ERA5."""
    
    def __init__(self, era5_file, output_dir):
        """
        Initialize the plotter.
        
        Args:
            era5_file: ERA5 NetCDF file
            output_dir: Directory to save plots
        """
        self.era5_file = PROJECT_ROOT / era5_file
        self.output_dir = PROJECT_ROOT / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Buoy locations to mark on plots
        # Real buoys: Itaguaí-RJ, Santos-SP, Florianópolis-SC
        # Fictitious buoys: B1, B2
        self.buoys = {
            'Itaguaí-RJ': {'lat': -23.48, 'lon': -43.98, 'type': 'real'},
            'Santos-SP': {'lat': -25.70, 'lon': -45.14, 'type': 'real'},
            'Florianópolis-SC': {'lat': -27.40, 'lon': -47.27, 'type': 'real'},
            'B1': {'lat': -30.0, 'lon': -40.0, 'type': 'fictitious'},
            'B2': {'lat': -25.0, 'lon': -37.5, 'type': 'fictitious'}
        }
        
        logger.info(f"📁 ERA5 data: {self.era5_file}")
        logger.info(f"📊 Output plots: {self.output_dir}")
        
        # Load data
        self.load_era5_data()
        self.calculate_daily_means()
    
    def load_era5_data(self):
        """Load ERA5 data."""
        logger.info("🌊 Loading ERA5 data...")
        
        try:
            self.era5_ds = xr.open_dataset(self.era5_file)
            
            # Rename time dimension if needed
            if 'valid_time' in self.era5_ds.dims:
                self.era5_ds = self.era5_ds.rename({'valid_time': 'time'})
            
            # Detect wave height variable
            if 'swh' in self.era5_ds.variables:
                self.era5_wave_var = 'swh'
            elif 'significant_height_of_combined_wind_waves_and_swell' in self.era5_ds.variables:
                self.era5_wave_var = 'significant_height_of_combined_wind_waves_and_swell'
            else:
                logger.error("❌ Wave height variable not found in ERA5")
                raise ValueError("No wave height variable in ERA5 dataset")
            
            logger.info(f"✅ ERA5 loaded: {len(self.era5_ds.time)} timesteps")
            logger.info(f"📊 Wave variable: {self.era5_wave_var}")
            
            # Get time range
            time_range = pd.to_datetime(self.era5_ds.time.values)
            logger.info(f"📅 Period: {time_range.min()} to {time_range.max()}")
            
        except Exception as e:
            logger.error(f"❌ Error loading ERA5: {e}")
            raise
    
    def calculate_daily_means(self):
        """Calculate daily mean wave heights."""
        logger.info("📊 Calculating daily means...")
        
        # Get wave height data
        swh = self.era5_ds[self.era5_wave_var]
        
        # Group by day and calculate mean
        self.daily_means = swh.groupby('time.date').mean('time')
        
        # Get unique dates
        self.dates = pd.to_datetime(self.daily_means.date.values)
        
        logger.info(f"✅ Calculated means for {len(self.dates)} days")
        logger.info(f"📅 Dates: {self.dates[0].strftime('%Y-%m-%d')} to {self.dates[-1].strftime('%Y-%m-%d')}")
    
    def create_daily_mean_plot(self):
        """Create subplot figure with all daily means."""
        logger.info("📊 Creating daily mean plot...")
        
        n_days = len(self.dates)
        
        # Determine subplot layout
        if n_days <= 5:
            nrows, ncols = 1, n_days
        elif n_days <= 10:
            nrows, ncols = 2, 5
        elif n_days <= 15:
            nrows, ncols = 3, 5
        elif n_days <= 20:
            nrows, ncols = 4, 5
        else:
            nrows = int(np.ceil(n_days / 5))
            ncols = 5
        
        logger.info(f"📐 Layout: {nrows} rows × {ncols} columns")
        
        # Create figure
        fig = plt.figure(figsize=(ncols * 4.5, nrows * 4))
        
        # Get data extent
        lons = self.era5_ds.longitude.values
        lats = self.era5_ds.latitude.values
        extent = [lons.min(), lons.max(), lats.min(), lats.max()]
        
        # Get global min/max for consistent colorbar
        vmin = float(self.daily_means.min())
        vmax = float(self.daily_means.max())
        
        logger.info(f"📊 Wave height range: {vmin:.2f} - {vmax:.2f} m")
        
        # Create subplots
        for idx, date in enumerate(self.dates):
            ax = plt.subplot(nrows, ncols, idx + 1, projection=ccrs.PlateCarree())
            
            # Get daily mean for this date (use isel with index instead of sel with date string)
            daily_data = self.daily_means.isel(date=idx)
            
            # Plot contourf
            im = ax.contourf(
                lons, lats, daily_data,
                levels=20,
                cmap='turbo',
                vmin=vmin,
                vmax=vmax,
                transform=ccrs.PlateCarree(),
                extend='both'
            )
            
            # Add geographic features
            ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
            ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', 
                          edgecolor='gray', alpha=0.7)
            
            # Set extent
            ax.set_extent(extent, crs=ccrs.PlateCarree())
            
            # Plot buoy locations
            for buoy_name, buoy_info in self.buoys.items():
                if buoy_info['type'] == 'real':
                    marker = '^'
                    color = 'blue'
                    size = 80
                    edgecolor = 'darkblue'
                else:  # fictitious
                    marker = 's'
                    color = 'orange'
                    size = 60
                    edgecolor = 'darkorange'
                
                ax.scatter(buoy_info['lon'], buoy_info['lat'],
                          marker=marker, s=size, c=color,
                          edgecolors=edgecolor, linewidths=1.5,
                          transform=ccrs.PlateCarree(), zorder=10)
            
            # Grid
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                             alpha=0.5, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            
            # Only show labels on left and bottom edges
            if idx % ncols != 0:
                gl.left_labels = False
            if idx < (nrows - 1) * ncols:
                gl.bottom_labels = False
            
            # Title with date
            ax.set_title(date.strftime('%Y-%m-%d'), fontsize=12, fontweight='bold')
        
        # Remove empty subplots if any
        total_subplots = nrows * ncols
        for idx in range(n_days, total_subplots):
            ax = plt.subplot(nrows, ncols, idx + 1)
            ax.axis('off')
        
        # Add colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = plt.colorbar(im, cax=cbar_ax, orientation='vertical')
        cbar.set_label('Daily Mean Significant Wave Height (m)', 
                      fontsize=14, fontweight='bold')
        cbar.ax.tick_params(labelsize=11)
        
        # Add legend for buoy markers
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='^', color='w', markerfacecolor='blue',
                   markeredgecolor='darkblue', markersize=10, linewidth=0,
                   label='Itaguaí-RJ, Santos-SP, Florianópolis-SC'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='orange',
                   markeredgecolor='darkorange', markersize=8, linewidth=0,
                   label='B1, B2')
        ]
        fig.legend(handles=legend_elements, loc='lower right',
                  bbox_to_anchor=(0.90, 0.02), fontsize=11,
                  framealpha=0.9, edgecolor='black')
        
        # Main title
        fig.suptitle(
            f'ERA5 Daily Mean Wave Heights\n'
            f'{self.dates[0].strftime("%Y-%m-%d")} to {self.dates[-1].strftime("%Y-%m-%d")}',
            fontsize=16, fontweight='bold', y=0.98
        )
        
        # Adjust layout
        plt.subplots_adjust(left=0.05, right=0.90, top=0.94, bottom=0.06, 
                           wspace=0.15, hspace=0.25)
        
        # Save figure
        start_date = self.dates[0].strftime('%Y%m%d')
        end_date = self.dates[-1].strftime('%Y%m%d')
        output_file = self.output_dir / f'era5_daily_means_{start_date}_{end_date}.png'
        
        logger.info(f"💾 Saving plot: {output_file}")
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"✅ Plot saved: {output_file}")
        
        return output_file


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("📊 ERA5 DAILY MEAN WAVE HEIGHTS")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure paths
    era5_file = 'data/era5_waves/era5_waves_akara_20240214_20240222.nc'
    output_dir = 'figures/era5_daily_means'
    
    # Check if ERA5 exists
    era5_path = PROJECT_ROOT / era5_file
    if not era5_path.exists():
        logger.error(f"❌ ERA5 file not found: {era5_path}")
        logger.info("💡 Run first: python scripts/download_era5_waves.py")
        return
    
    # Create plotter
    plotter = ERA5DailyMeanPlotter(era5_file, output_dir)
    
    # Create plot
    plotter.create_daily_mean_plot()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ PLOT COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"📁 Saved in: {plotter.output_dir}")
    logger.info("")
    logger.info("💡 Next steps:")
    logger.info("   - Review daily mean plot")
    logger.info("   - Compare with satellite observations")
    logger.info("   - Analyze temporal evolution")


if __name__ == "__main__":
    main()
