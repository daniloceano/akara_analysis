#!/usr/bin/env python3
"""
Compare ERA5 and satellite altimetry data at buoy locations.

Creates time series plots showing:
- ERA5 significant wave height (black line)
- Satellite altimetry observations (colored points by satellite)

For each buoy location, creates 4 plots with different distance thresholds:
5km, 10km, 20km, and 50km.

For each satellite pass within a given hour, only the closest point to the
buoy is retained.

Author: GitHub Copilot + Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import warnings
import logging
from typing import Dict, Tuple

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class BuoyLocationComparator:
    """Compare ERA5 and satellite data at buoy locations."""
    
    def __init__(self, data_dir, era5_file, output_dir):
        """
        Initialize the comparator.
        
        Args:
            data_dir: Directory with satellite data (CSV)
            era5_file: ERA5 NetCDF file
            output_dir: Directory to save plots
        """
        self.data_dir = PROJECT_ROOT / data_dir
        self.era5_file = PROJECT_ROOT / era5_file
        self.output_dir = PROJECT_ROOT / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Buoy locations
        # Real buoys: Itaguaí-RJ, Santos-SP, Florianópolis-SC
        # Fictitious buoys: B1, B2
        self.buoys = {
            'Itaguai-RJ': {'lat': -23.48, 'lon': -43.98},
            'Santos-SP': {'lat': -25.70, 'lon': -45.14},
            'Florianopolis-SC': {'lat': -27.40, 'lon': -47.27},
            'B1': {'lat': -30.0, 'lon': -40.0},
            'B2': {'lat': -25.0, 'lon': -37.5}
        }
        
        # Distance thresholds (km)
        self.distance_thresholds = [5, 10, 20, 50]
        
        # Satellite colors (matching animation script)
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
            'SWOT/nadir': '#FF69B4',
        }
        
        logger.info(f"📁 Satellite data: {self.data_dir}")
        logger.info(f"📁 ERA5 data: {self.era5_file}")
        logger.info(f"📊 Output plots: {self.output_dir}")
        logger.info(f"🎯 Buoy locations: {list(self.buoys.keys())}")
        logger.info(f"📏 Distance thresholds: {self.distance_thresholds} km")
        
        # Configure plotting style
        self.setup_plotting_style()
        
        # Load data
        self.load_era5_data()
        self.load_satellite_data()
    
    def setup_plotting_style(self):
        """Configure professional plotting style."""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams.update({
            'font.size': 11,
            'font.family': 'sans-serif',
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 9,
            'figure.titlesize': 16,
            'axes.linewidth': 1.2,
            'grid.linewidth': 0.6,
            'lines.linewidth': 2,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
        })
    
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
            logger.info(f"📅 Period: {pd.to_datetime(self.era5_ds.time.min().values)} to {pd.to_datetime(self.era5_ds.time.max().values)}")
            
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
                df['time'] = pd.to_datetime(df['time'], utc=True)
                
                # Filter only VAVH (significant wave height)
                df_vavh = df[df['variable'] == 'VAVH'].copy()
                
                if len(df_vavh) > 0:
                    # Friendly name (remove underscore from Saral)
                    sat_name = sat.replace('_', '/')
                    self.satellite_data[sat_name] = df_vavh
                    logger.info(f"✅ {sat_name}: {len(df_vavh)} VAVH points")
                
            except Exception as e:
                logger.error(f"❌ Error loading {sat}: {e}")
        
        logger.info(f"📊 Total: {len(self.satellite_data)} satellites loaded")
    
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate haversine distance between two points in kilometers.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        R = 6371.0  # Earth radius in km
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlon_rad = np.radians(lon2 - lon1)
        dlat_rad = np.radians(lat2 - lat1)
        
        a = np.sin(dlat_rad/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon_rad/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def extract_era5_timeseries(self, buoy_name: str) -> pd.DataFrame:
        """
        Extract ERA5 time series at buoy location.
        
        Args:
            buoy_name: Name of the buoy
            
        Returns:
            DataFrame with time and swh columns
        """
        buoy = self.buoys[buoy_name]
        
        # Find nearest grid point
        era5_data = self.era5_ds[self.era5_wave_var].sel(
            latitude=buoy['lat'],
            longitude=buoy['lon'],
            method='nearest'
        )
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': pd.to_datetime(self.era5_ds.time.values),
            'swh': era5_data.values
        })
        
        # Ensure UTC timezone
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
        
        logger.info(f"✅ ERA5 at {buoy_name}: {len(df)} points, "
                   f"SWH range {df['swh'].min():.2f}-{df['swh'].max():.2f} m")
        
        return df
    
    def filter_satellite_data(self, buoy_name: str, 
                             max_distance_km: float) -> Dict[str, pd.DataFrame]:
        """
        Filter satellite data by distance from buoy.
        
        For each satellite and each hour, keeps only the closest observation.
        
        Args:
            buoy_name: Name of the buoy
            max_distance_km: Maximum distance threshold in km
            
        Returns:
            Dictionary {satellite_name: filtered_dataframe}
        """
        buoy = self.buoys[buoy_name]
        filtered_data = {}
        
        for sat_name, df in self.satellite_data.items():
            # Calculate distances
            df = df.copy()
            df['distance_km'] = self.haversine_distance(
                buoy['lat'], buoy['lon'],
                df['latitude'].values, df['longitude'].values
            )
            
            # Filter by distance
            df_close = df[df['distance_km'] <= max_distance_km].copy()
            
            if len(df_close) == 0:
                continue
            
            # Group by hour and keep closest observation
            df_close['hour'] = df_close['time'].dt.floor('H')
            
            # For each hour, find the observation with minimum distance
            idx_closest = df_close.groupby('hour')['distance_km'].idxmin()
            df_filtered = df_close.loc[idx_closest].copy()
            
            filtered_data[sat_name] = df_filtered
            
            logger.info(f"  {sat_name}: {len(df_close)} within {max_distance_km}km → "
                       f"{len(df_filtered)} after hourly filtering")
        
        return filtered_data
    
    def create_comparison_plot(self, buoy_name: str, distance_km: float):
        """
        Create time series comparison plot.
        
        Args:
            buoy_name: Name of the buoy
            distance_km: Distance threshold in km
        """
        logger.info(f"📊 Creating plot: {buoy_name} @ {distance_km}km")
        
        # Extract ERA5 data
        era5_df = self.extract_era5_timeseries(buoy_name)
        
        # Filter satellite data
        sat_data = self.filter_satellite_data(buoy_name, distance_km)
        
        if len(sat_data) == 0:
            logger.warning(f"⚠️ No satellite data within {distance_km}km for {buoy_name}")
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Plot ERA5 time series (black line)
        ax.plot(era5_df['time'], era5_df['swh'], 
               color='black', linewidth=2, label='ERA5', zorder=1)
        
        # Plot satellite observations (colored points)
        for sat_name, df in sat_data.items():
            color = self.satellite_colors.get(sat_name, '#888888')
            ax.scatter(df['time'], df['value'], 
                      color=color, s=40, alpha=0.8, 
                      label=sat_name, zorder=2,
                      edgecolors='white', linewidths=0.5)
        
        # Configure plot
        buoy = self.buoys[buoy_name]
        ax.set_xlabel('Time (UTC)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Significant Wave Height (m)', fontsize=12, fontweight='bold')
        ax.set_title(
            f'{buoy_name} ({buoy["lat"]:.2f}°S, {abs(buoy["lon"]):.2f}°W)\n'
            f'ERA5 vs Satellite Altimetry - Distance threshold: {distance_km} km',
            fontsize=14, fontweight='bold', pad=15
        )
        
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', ncol=3, framealpha=0.9, fontsize=9)
        
        # Format x-axis
        ax.tick_params(axis='x', rotation=45)
        fig.autofmt_xdate()
        
        # Set y-axis limits
        ax.set_ylim(bottom=0)
        
        # Save figure
        filename = f'comparison_{buoy_name.replace("-", "_")}_{distance_km}km.png'
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"✅ Saved: {output_path}")
        
        # Print statistics
        total_sat_obs = sum(len(df) for df in sat_data.values())
        logger.info(f"   ERA5 points: {len(era5_df)}, "
                   f"Satellite obs: {total_sat_obs} from {len(sat_data)} satellites")
    
    def create_all_comparisons(self):
        """Create all comparison plots (3 buoys × 4 thresholds = 12 plots)."""
        logger.info("=" * 60)
        logger.info("🎯 CREATING ALL COMPARISON PLOTS")
        logger.info("=" * 60)
        
        total_plots = len(self.buoys) * len(self.distance_thresholds)
        plot_count = 0
        
        for buoy_name in self.buoys.keys():
            logger.info("")
            logger.info(f"🎯 Buoy: {buoy_name}")
            logger.info("-" * 60)
            
            for distance_km in self.distance_thresholds:
                plot_count += 1
                logger.info(f"\n[{plot_count}/{total_plots}] Distance threshold: {distance_km} km")
                
                try:
                    self.create_comparison_plot(buoy_name, distance_km)
                except Exception as e:
                    logger.error(f"❌ Error creating plot: {e}")
                    continue
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✅ COMPLETE! Created {plot_count} plots")
        logger.info(f"📁 Saved in: {self.output_dir}")
        logger.info("=" * 60)


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("📊 BUOY LOCATION COMPARISON - ERA5 vs SATELLITES")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure paths
    data_dir = 'data'
    era5_file = 'data/era5_waves/era5_waves_akara_20240214_20240222.nc'
    output_dir = 'figures/buoy_comparisons'
    
    # Check if ERA5 exists
    era5_path = PROJECT_ROOT / era5_file
    if not era5_path.exists():
        logger.error(f"❌ ERA5 file not found: {era5_path}")
        logger.info("💡 Run first: python scripts/download_era5_waves.py")
        return
    
    # Create comparator
    comparator = BuoyLocationComparator(data_dir, era5_file, output_dir)
    
    # Create all comparison plots
    comparator.create_all_comparisons()
    
    logger.info("")
    logger.info("💡 Next steps:")
    logger.info("   - Review plots in figures/buoy_comparisons/")
    logger.info("   - Analyze differences between distance thresholds")
    logger.info("   - Compare satellite vs ERA5 performance")


if __name__ == "__main__":
    main()
