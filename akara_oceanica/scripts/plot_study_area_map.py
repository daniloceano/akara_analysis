#!/usr/bin/env python3
"""
Plot study area map showing buoy locations and Akará cyclone track.

Shows:
- Geographic boundaries of the Akará study region
- Real buoy locations (Itaguaí-RJ, Santos-SP, Florianópolis-SC)
- Fictitious buoy locations (B1, B2)
- Akará cyclone track with temporal evolution

Author: Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
"""

import numpy as np
import pandas as pd
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


class StudyAreaMapper:
    """Create study area map with buoy locations and cyclone track."""
    
    def __init__(self, track_file, output_dir):
        """
        Initialize the mapper.
        
        Args:
            track_file: CSV file with Akará track
            output_dir: Directory to save map
        """
        self.track_file = PROJECT_ROOT / track_file
        self.output_dir = PROJECT_ROOT / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Buoy locations
        # Real buoys: Itaguaí-RJ, Santos-SP, Florianópolis-SC
        # Fictitious buoys: B1, B2
        self.buoys = {
            'Itaguaí-RJ': {'lat': -23.48, 'lon': -43.98, 'type': 'real'},
            'Santos-SP': {'lat': -25.70, 'lon': -45.14, 'type': 'real'},
            'Florianópolis-SC': {'lat': -27.40, 'lon': -47.27, 'type': 'real'},
            'B1': {'lat': -30.0, 'lon': -40.0, 'type': 'fictitious'},
            'B2': {'lat': -25.0, 'lon': -37.5, 'type': 'fictitious'}
        }
        
        # Study area boundaries (Akará region)
        self.region = {
            'west': -50.0,
            'east': -20.0,
            'south': -45.0,
            'north': -15.0
        }
        
        logger.info(f"📁 Track file: {self.track_file}")
        logger.info(f"📊 Output map: {self.output_dir}")
        logger.info(f"🎯 Buoys: {len(self.buoys)} ({sum(1 for b in self.buoys.values() if b['type']=='real')} real, "
                   f"{sum(1 for b in self.buoys.values() if b['type']=='fictitious')} fictitious)")
        
        # Load track data
        self.load_track_data()
    
    def load_track_data(self):
        """Load Akará cyclone track."""
        logger.info("🌀 Loading Akará track...")
        
        try:
            # Read CSV with semicolon separator
            self.track_df = pd.read_csv(self.track_file, sep=';')
            
            # Parse time column
            self.track_df['datetime'] = pd.to_datetime(
                self.track_df['time'], 
                format='%Y-%m-%d-%H%M'
            )
            
            # Sort by time
            self.track_df = self.track_df.sort_values('datetime')
            
            logger.info(f"✅ Track loaded: {len(self.track_df)} positions")
            logger.info(f"📅 Period: {self.track_df['datetime'].min()} to {self.track_df['datetime'].max()}")
            logger.info(f"📍 Lat range: {self.track_df['Lat'].min():.2f}° to {self.track_df['Lat'].max():.2f}°")
            logger.info(f"📍 Lon range: {self.track_df['Lon'].min():.2f}° to {self.track_df['Lon'].max():.2f}°")
            
        except Exception as e:
            logger.error(f"❌ Error loading track: {e}")
            raise
    
    def create_study_area_map(self):
        """Create study area map."""
        logger.info("🗺️ Creating study area map...")
        
        # Create figure
        fig = plt.figure(figsize=(14, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Set extent
        ax.set_extent([
            self.region['west'],
            self.region['east'],
            self.region['south'],
            self.region['north']
        ], crs=ccrs.PlateCarree())
        
        # Add geographic features
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', 
                      linewidth=0.8, zorder=1)
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3, zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=1.2, edgecolor='black', zorder=2)
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, linestyle='--', 
                      edgecolor='gray', alpha=0.7, zorder=2)
        
        # Add states/provinces for Brazil
        ax.add_feature(cfeature.STATES, linewidth=0.5, linestyle=':', 
                      edgecolor='darkgray', alpha=0.5, zorder=2)
        
        # Plot Akará track
        track_lons = self.track_df['Lon'].values
        track_lats = self.track_df['Lat'].values
        
        # Plot track line
        ax.plot(track_lons, track_lats, 
               color='red', linewidth=3, marker='o', markersize=5,
               transform=ccrs.PlateCarree(), zorder=5,
               label='Akará Track', alpha=0.8)
        
        # Mark start and end positions
        ax.plot(track_lons[0], track_lats[0], 
               marker='*', markersize=20, color='green',
               markeredgecolor='black', markeredgewidth=1.5,
               transform=ccrs.PlateCarree(), zorder=6,
               label='Start')
        
        ax.plot(track_lons[-1], track_lats[-1], 
               marker='X', markersize=18, color='purple',
               markeredgecolor='black', markeredgewidth=1.5,
               transform=ccrs.PlateCarree(), zorder=6,
               label='End')
        
        # Plot buoy locations
        for buoy_name, buoy_info in self.buoys.items():
            if buoy_info['type'] == 'real':
                marker = '^'
                color = 'blue'
                size = 150
                edgecolor = 'darkblue'
            else:  # fictitious
                marker = 's'
                color = 'orange'
                size = 120
                edgecolor = 'darkorange'
            
            ax.scatter(buoy_info['lon'], buoy_info['lat'],
                      marker=marker, s=size, c=color,
                      edgecolors=edgecolor, linewidths=2,
                      transform=ccrs.PlateCarree(), zorder=7,
                      label=buoy_name)
            
            # Add buoy label
            ax.text(buoy_info['lon'] + 0.5, buoy_info['lat'] + 0.3,
                   buoy_name,
                   fontsize=10, fontweight='bold',
                   transform=ccrs.PlateCarree(), zorder=8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='black', alpha=0.8))
        
        # Add gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=1, color='gray', 
                         alpha=0.5, linestyle='--', zorder=3)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 11, 'weight': 'bold'}
        gl.ylabel_style = {'size': 11, 'weight': 'bold'}
        
        # Title
        ax.set_title(
            f'Study Area Map - Akará Cyclone\n'
            f'Buoy Locations and Cyclone Track\n'
            f'{self.track_df["datetime"].min().strftime("%Y-%m-%d")} to '
            f'{self.track_df["datetime"].max().strftime("%Y-%m-%d")}',
            fontsize=16, fontweight='bold', pad=20
        )
        
        # Legend
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9,
                 edgecolor='black', fancybox=True, shadow=True)
        
        # Add info text box
        info_text = (
            f"Buoy Locations: 5\n"
            f"Track Points: {len(self.track_df)}"
        )
        ax.text(0.02, 0.02, info_text,
               transform=ax.transAxes,
               fontsize=10, verticalalignment='bottom',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor='black', alpha=0.9))
        
        # Save figure
        output_file = self.output_dir / 'study_area_map_buoys_track.png'
        
        logger.info(f"💾 Saving map: {output_file}")
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"✅ Map saved: {output_file}")
        
        return output_file


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("🗺️ STUDY AREA MAP - BUOYS AND CYCLONE TRACK")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure paths
    track_file = 'data/track_akara'
    output_dir = 'figures/maps'
    
    # Check if track file exists
    track_path = PROJECT_ROOT / track_file
    if not track_path.exists():
        logger.error(f"❌ Track file not found: {track_path}")
        return
    
    # Create mapper
    mapper = StudyAreaMapper(track_file, output_dir)
    
    # Create map
    mapper.create_study_area_map()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ MAP COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"📁 Saved in: {mapper.output_dir}")
    logger.info("")
    logger.info("💡 Use this map to:")
    logger.info("   - Visualize study area boundaries")
    logger.info("   - Identify buoy locations (real and fictitious)")
    logger.info("   - Understand cyclone trajectory")


if __name__ == "__main__":
    main()
