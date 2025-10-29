"""
Advanced script to plot satellite trajectories with enhanced visualization
Includes wave height heatmap and detailed trajectories
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from datetime import datetime
import logging
from config import START_DATE, END_DATE, BBOX, DATASETS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretório base do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cores para cada satélite (igual à figura de referência)
SATELLITE_COLORS = {
    'CFOSAT': '#00FFFF',        # Cyan
    'CryoSat-2': '#FF1493',     # Deep Pink
    'HaiYang-2B': '#FFD700',    # Gold
    'HaiYang-2C': '#FF8C00',    # Dark Orange
    'Jason-3': '#00FFFF',       # Cyan (como na figura)
    'Saral/AltiKa': '#FF0000',  # Red
    'Sentinel-3A': '#FFFF00',   # Yellow
    'Sentinel-3B': '#00CED1',   # Dark Turquoise
    'Sentinel-6A': '#9370DB',   # Medium Purple
    'SWOT_nadir': '#FFFF00',    # Yellow (como SWOT na figura)
}


def load_satellite_data(data_dir='data'):
    """
    Load data from all available satellites
    """
    data_path = PROJECT_ROOT / data_dir
    satellite_data = {}
    
    logger.info("🔍 Searching for satellite data...")
    
    for satellite in DATASETS.keys():
        satellite_dir = data_path / satellite.replace('/', '_')
        
        if not satellite_dir.exists():
            logger.warning(f"⚠️  Directory not found: {satellite}")
            continue
        
        # Search for CSV file (copernicusmarine format)
        csv_files = list(satellite_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"⚠️  No CSV file found for {satellite}")
            continue
        
        csv_file = csv_files[0]
        try:
            df = pd.read_csv(csv_file)
            
            if len(df) > 0:
                # Convert time to datetime
                df['time'] = pd.to_datetime(df['time'])
                satellite_data[satellite] = df
                logger.info(f"✅ {satellite}: {len(df)} points loaded")
            else:
                logger.warning(f"⚠️  {satellite}: no data in region")
                
        except Exception as e:
            logger.error(f"❌ Error loading {satellite}: {str(e)}")
    
    return satellite_data


def plot_satellite_tracks_advanced(satellite_data, output_file='figures/satellite_tracks_advanced.png'):
    """
    Plot trajectories with advanced visualization (wave height colors)
    """
    logger.info("🎨 Creating advanced figure...")
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Map limits
    margin = 1.0
    ax.set_extent([
        BBOX['west'] - margin,
        BBOX['east'] + margin,
        BBOX['south'] - margin,
        BBOX['north'] + margin
    ], crs=ccrs.PlateCarree())
    
    # Geographic features with style similar to reference figure
    ax.add_feature(cfeature.LAND, facecolor='#2d5016', zorder=1)
    ax.add_feature(cfeature.OCEAN, facecolor='#08306b', zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='white', zorder=2)
    
    # Grid
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='white', alpha=0.3, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}
    
    # Prepare normalization for wave height colormap
    all_wave_heights = []
    for df in satellite_data.values():
        df_vavh = df[df['variable'] == 'VAVH']
        if 'value' in df_vavh.columns:
            wh = df_vavh['value'].values
            all_wave_heights.extend(wh[~np.isnan(wh)])
    
    if all_wave_heights:
        vmin, vmax = 0, max(all_wave_heights)
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.turbo
    else:
        norm = None
        cmap = None
    
    # Plot trajectory for each satellite
    for satellite, df in satellite_data.items():
        color = SATELLITE_COLORS.get(satellite, '#FFFFFF')
        
        try:
            # Filter only VAVH data
            df_vavh = df[df['variable'] == 'VAVH'].copy()
            
            if len(df_vavh) == 0:
                logger.warning(f"⚠️  {satellite}: no VAVH data")
                continue
            
            lons = df_vavh['longitude'].values
            lats = df_vavh['latitude'].values
            times = df_vavh['time'].values
            
            # Get wave heights
            wave_heights = df_vavh['value'].values if 'value' in df_vavh.columns else None
            
            # Remove NaNs
            if wave_heights is not None:
                valid_mask = ~(np.isnan(lons) | np.isnan(lats) | np.isnan(wave_heights))
            else:
                valid_mask = ~(np.isnan(lons) | np.isnan(lats))
            
            lons = lons[valid_mask]
            lats = lats[valid_mask]
            times = times[valid_mask]
            
            if wave_heights is not None:
                wave_heights = wave_heights[valid_mask]
            
            if len(lons) == 0:
                continue
            
            # Plot trajectory points colored by wave height
            if wave_heights is not None and norm is not None:
                # Color by wave height
                scatter = ax.scatter(lons, lats, c=wave_heights, s=40, alpha=0.8,
                                   cmap=cmap, norm=norm,
                                   transform=ccrs.PlateCarree(),
                                   edgecolors='black', linewidth=0.3, zorder=5)
            else:
                # Use satellite color
                ax.scatter(lons, lats, c=color, s=40, alpha=0.8,
                         transform=ccrs.PlateCarree(),
                         edgecolors='black', linewidth=0.3, zorder=5)
            
            # Labels with dates and product
            if len(times) > 0:
                # Start of trajectory
                date_start = pd.to_datetime(times[0])
                label_start = f"{satellite.split('/')[0][:3].upper()}\n{date_start.day}.M.{date_start.strftime('%H')}h"
                
                ax.text(lons[0], lats[0], label_start,
                       fontsize=8, ha='center', va='bottom',
                       color='white', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor=color,
                               alpha=0.9, edgecolor='black', linewidth=1.5),
                       transform=ccrs.PlateCarree(), zorder=7)
                
                # End of trajectory (if enough points)
                if len(times) > 10:
                    date_end = pd.to_datetime(times[-1])
                    label_end = f"{date_end.day}.M.{date_end.strftime('%H')}h"
                    
                    ax.text(lons[-1], lats[-1], label_end,
                           fontsize=7, ha='center', va='top',
                           color='white', fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=color,
                                   alpha=0.8, edgecolor='black', linewidth=1),
                           transform=ccrs.PlateCarree(), zorder=7)
            
            logger.info(f"✅ Plotted {satellite}: {len(lons)} points")
            
        except Exception as e:
            logger.error(f"❌ Error plotting {satellite}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Add colorbar if wave height data available
    if norm is not None:
        cbar = plt.colorbar(scatter, ax=ax, orientation='vertical', 
                           pad=0.05, shrink=0.8, aspect=30)
        cbar.set_label('Significant Wave Height (m)', fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
    
    # Title
    plt.title(f'Satellite Passes - Akará Cyclone\n{START_DATE} to {END_DATE}',
              fontsize=16, fontweight='bold', pad=20)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save
    output_path = PROJECT_ROOT / output_file
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"💾 Figure saved: {output_path}")
    
    plt.close(fig)
    
    return fig, ax


def main():
    """
    Main function
    """
    logger.info("=" * 60)
    logger.info("🗺️  ADVANCED PLOTTING - AKARÁ CYCLONE 🌊")
    logger.info("=" * 60)
    logger.info("")
    
    # Load data
    satellite_data = load_satellite_data()
    
    if not satellite_data:
        logger.error("❌ No data found! Run download_satellite_data.py first")
        logger.info("\n💡 Tip: Run download with:")
        logger.info("   python scripts/download_satellite_data.py")
        return
    
    logger.info(f"\n📊 Total satellites with data: {len(satellite_data)}")
    logger.info("")
    
    # Plot overview
    plot_satellite_tracks_advanced(satellite_data)
    
    # Plot daily panels
    plot_daily_panels(satellite_data)
    
    logger.info("")
    logger.info("🎉 Processing complete! 🚀")


def plot_daily_panels(satellite_data, output_file='figures/satellite_tracks_daily.png'):
    """
    Create figure with separate panels per day showing satellite passes
    """
    logger.info("📅 Creating daily panels...")
    
    # Collect all unique dates
    all_dates = set()
    for df in satellite_data.values():
        df_vavh = df[df['variable'] == 'VAVH']
        if len(df_vavh) > 0:
            dates = pd.to_datetime(df_vavh['time']).dt.date
            all_dates.update(dates)
    
    all_dates = sorted(list(all_dates))
    
    if len(all_dates) == 0:
        logger.warning("⚠️  No dates found")
        return
    
    logger.info(f"📆 Dates found: {len(all_dates)} days")
    
    # Calculate grid layout (try to make it square)
    n_days = len(all_dates)
    ncols = int(np.ceil(np.sqrt(n_days)))
    nrows = int(np.ceil(n_days / ncols))
    
    # Create figure with subplots
    fig = plt.figure(figsize=(6 * ncols, 5 * nrows))
    
    # Prepare normalization for colormap
    all_wave_heights = []
    for df in satellite_data.values():
        df_vavh = df[df['variable'] == 'VAVH']
        if 'value' in df_vavh.columns:
            wh = df_vavh['value'].values
            all_wave_heights.extend(wh[~np.isnan(wh)])
    
    if all_wave_heights:
        vmin, vmax = 0, max(all_wave_heights)
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.turbo
    else:
        vmin, vmax = 0, 8
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.cm.turbo
    
    # Create panel for each day
    for idx, date in enumerate(all_dates):
        ax = fig.add_subplot(nrows, ncols, idx + 1, projection=ccrs.PlateCarree())
        
        # Map limits
        margin = 1.0
        ax.set_extent([
            BBOX['west'] - margin,
            BBOX['east'] + margin,
            BBOX['south'] - margin,
            BBOX['north'] + margin
        ], crs=ccrs.PlateCarree())
        
        # Geographic features
        ax.add_feature(cfeature.LAND, facecolor='#e0e0e0', zorder=1)
        ax.add_feature(cfeature.OCEAN, facecolor='#d4e6f1', zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black', zorder=2)
        
        # Grid
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color='gray', 
                         alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}
        
        # Plot data for this day
        day_has_data = False
        for satellite, df in satellite_data.items():
            df_vavh = df[df['variable'] == 'VAVH'].copy()
            
            if len(df_vavh) == 0:
                continue
            
            # Filter by date
            df_vavh['date'] = pd.to_datetime(df_vavh['time']).dt.date
            df_day = df_vavh[df_vavh['date'] == date]
            
            if len(df_day) == 0:
                continue
            
            day_has_data = True
            
            lons = df_day['longitude'].values
            lats = df_day['latitude'].values
            wave_heights = df_day['value'].values if 'value' in df_day.columns else None
            
            # Remove NaNs
            if wave_heights is not None:
                valid_mask = ~(np.isnan(lons) | np.isnan(lats) | np.isnan(wave_heights))
                lons = lons[valid_mask]
                lats = lats[valid_mask]
                wave_heights = wave_heights[valid_mask]
            else:
                valid_mask = ~(np.isnan(lons) | np.isnan(lats))
                lons = lons[valid_mask]
                lats = lats[valid_mask]
            
            if len(lons) == 0:
                continue
            
            # Plot points colored by wave height
            scatter = ax.scatter(lons, lats, c=wave_heights, s=30, alpha=0.8,
                               cmap=cmap, norm=norm,
                               transform=ccrs.PlateCarree(),
                               edgecolors='black', linewidth=0.3, zorder=5)
        
        # Panel title
        date_str = pd.to_datetime(date).strftime('%d/%m/%Y')
        ax.set_title(f'{date_str}', fontsize=12, fontweight='bold', pad=8)
        
        # Indicator if no data
        if not day_has_data:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                   ha='center', va='center', fontsize=14, color='gray', alpha=0.5)
    
    # Add shared colorbar
    if all_wave_heights:
        # Create axis for colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap),
                           cax=cbar_ax, orientation='vertical')
        cbar.set_label('Significant Wave Height (m)', fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
    
    # General title
    fig.suptitle(f'Satellite Passes per Day - Akará Cyclone\n{START_DATE} to {END_DATE}',
                fontsize=16, fontweight='bold', y=0.98)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 0.90, 0.96])
    
    # Save
    output_path = PROJECT_ROOT / output_file
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"💾 Daily figure saved: {output_path}")
    
    plt.close(fig)
    
    return fig


if __name__ == "__main__":
    main()
