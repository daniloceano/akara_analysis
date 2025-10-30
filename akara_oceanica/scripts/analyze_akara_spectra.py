"""
Focused analysis of wave spectra during Akará cyclone.

This script filters and analyzes wave spectra data specifically for the
Akará cyclone region and time period (Feb 12-16, 2024).
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Try different import methods
try:
    from scripts.analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser
    from scripts.analyze_wave_spectra import analyze_swim_data, analyze_sar_data
    from scripts.plot_wave_spectra import plot_polar_spectrum, plot_spectrum_grid
except ModuleNotFoundError:
    from analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser
    from analyze_wave_spectra import analyze_swim_data, analyze_sar_data
    from scripts.plot_wave_spectra import plot_polar_spectrum, plot_spectrum_grid


# Akará cyclone region and time period
AKARA_LAT_MIN, AKARA_LAT_MAX = -45.0, -20.0
AKARA_LON_MIN, AKARA_LON_MAX = -50.0, -30.0
AKARA_START = datetime(2024, 2, 12)
AKARA_END = datetime(2024, 2, 16, 23, 59)


def filter_akara_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter data for Akará cyclone region and time.
    
    Args:
        df: DataFrame with wave analysis results (lon already in -180 to 180 format)
        
    Returns:
        Filtered DataFrame
    """
    df = df.copy()
    
    # Filter by region and time (lon is already in -180 to 180 format from analysis)
    mask = (
        (df['lon'] >= AKARA_LON_MIN) &
        (df['lon'] <= AKARA_LON_MAX) &
        (df['lat'] >= AKARA_LAT_MIN) &
        (df['lat'] <= AKARA_LAT_MAX) &
        (df['datetime'] >= AKARA_START) &
        (df['datetime'] <= AKARA_END)
    )
    
    df_filtered = df[mask].copy()
    
    return df_filtered


def plot_akara_comparison(swim_df: pd.DataFrame, sar_df: pd.DataFrame, 
                          output_file: str = None):
    """
    Compare SWIM and SAR data for Akará cyclone.
    
    Args:
        swim_df: SWIM analysis results
        sar_df: SAR analysis results
        output_file: Path to save figure
    """
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('Wave Analysis - Akará Cyclone (Feb 12-16, 2024)\nCFOSAT SWIM vs Sentinel-1A SAR', 
                 fontsize=14, fontweight='bold')
    
    # 1. SWH comparison
    ax1 = fig.add_subplot(gs[0, :])
    if len(swim_df) > 0:
        ax1.plot(swim_df['datetime'], swim_df['swh_total'], 'o-', 
                color='#1f77b4', linewidth=2, markersize=6, 
                label='SWIM Total SWH', alpha=0.7)
        ax1.plot(swim_df['datetime'], swim_df['swh_wind_sea'], 's-', 
                color='#ff7f0e', linewidth=1.5, markersize=4, 
                label='SWIM Wind Sea', alpha=0.6)
        ax1.plot(swim_df['datetime'], swim_df['swh_swell'], '^-', 
                color='#2ca02c', linewidth=1.5, markersize=4, 
                label='SWIM Swell', alpha=0.6)
    
    if len(sar_df) > 0:
        ax1.plot(sar_df['datetime'], sar_df['swh_total'], 'd-', 
                color='#d62728', linewidth=2, markersize=6, 
                label='SAR Total SWH', alpha=0.7)
        ax1.plot(sar_df['datetime'], sar_df['swh_wind_sea'], 'v-', 
                color='#9467bd', linewidth=1.5, markersize=4, 
                label='SAR Wind Sea', alpha=0.6)
        ax1.plot(sar_df['datetime'], sar_df['swh_swell'], 'p-', 
                color='#8c564b', linewidth=1.5, markersize=4, 
                label='SAR Swell', alpha=0.6)
    
    ax1.set_ylabel('Significant Wave Height (m)', fontsize=11, fontweight='bold')
    ax1.set_title('Wave Height Evolution', fontsize=12, fontweight='bold')
    ax1.legend(loc='best', ncol=3, frameon=True, fancybox=True, shadow=True, fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Peak Period comparison
    ax2 = fig.add_subplot(gs[1, 0])
    if len(swim_df) > 0:
        ax2.plot(swim_df['datetime'], swim_df['tp'], 'o-', 
                color='#1f77b4', linewidth=2, markersize=6, label='SWIM')
    if len(sar_df) > 0:
        ax2.plot(sar_df['datetime'], sar_df['tp'], 'd-', 
                color='#d62728', linewidth=2, markersize=6, label='SAR')
    ax2.set_ylabel('Peak Period (s)', fontsize=11, fontweight='bold')
    ax2.set_title('Peak Period', fontsize=12, fontweight='bold')
    ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Mean Direction comparison
    ax3 = fig.add_subplot(gs[1, 1])
    if len(swim_df) > 0:
        ax3.plot(swim_df['datetime'], swim_df['mean_dir'], 'o-', 
                color='#1f77b4', linewidth=2, markersize=6, label='SWIM')
    if len(sar_df) > 0:
        ax3.plot(sar_df['datetime'], sar_df['mean_dir'], 'd-', 
                color='#d62728', linewidth=2, markersize=6, label='SAR')
    ax3.set_ylabel('Mean Direction (°)', fontsize=11, fontweight='bold')
    ax3.set_title('Wave Direction', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, 360)
    ax3.set_yticks([0, 90, 180, 270, 360])
    ax3.set_yticklabels(['N (0°)', 'E (90°)', 'S (180°)', 'W (270°)', 'N (360°)'])
    ax3.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Spatial distribution map
    ax4 = fig.add_subplot(gs[2, :], projection=ccrs.PlateCarree())
    ax4.coastlines(resolution='10m', linewidth=1.0)
    ax4.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
    ax4.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.2)
    ax4.gridlines(draw_labels=True, alpha=0.3, linestyle='--')
    ax4.set_extent([AKARA_LON_MIN, AKARA_LON_MAX, AKARA_LAT_MIN, AKARA_LAT_MAX])
    
    # Plot measurements
    if len(swim_df) > 0:
        sc1 = ax4.scatter(swim_df['lon'], swim_df['lat'], 
                         c=swim_df['swh_total'], s=80, cmap='turbo',
                         vmin=0, vmax=max(swim_df['swh_total'].max(), sar_df['swh_total'].max()) if len(sar_df) > 0 else swim_df['swh_total'].max(),
                         edgecolors='blue', linewidths=1.5, alpha=0.7,
                         marker='o', label='SWIM',
                         transform=ccrs.PlateCarree())
    
    if len(sar_df) > 0:
        sc2 = ax4.scatter(sar_df['lon'], sar_df['lat'], 
                         c=sar_df['swh_total'], s=100, cmap='turbo',
                         vmin=0, vmax=max(swim_df['swh_total'].max(), sar_df['swh_total'].max()) if len(swim_df) > 0 else sar_df['swh_total'].max(),
                         edgecolors='red', linewidths=1.5, alpha=0.7,
                         marker='d', label='SAR',
                         transform=ccrs.PlateCarree())
    
    ax4.set_title('Measurement Locations - SWH (m)', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    
    # Add colorbar
    if len(swim_df) > 0 or len(sar_df) > 0:
        cbar = plt.colorbar(sc1 if len(swim_df) > 0 else sc2, ax=ax4, 
                           shrink=0.6, pad=0.05)
        cbar.set_label('SWH (m)', fontsize=10)
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def plot_akara_statistics(swim_df: pd.DataFrame, sar_df: pd.DataFrame,
                          output_file: str = None):
    """
    Plot statistical comparison for Akará data.
    
    Args:
        swim_df: SWIM data for Akará
        sar_df: SAR data for Akará
        output_file: Path to save figure
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Statistical Comparison - Akará Cyclone Region', 
                 fontsize=14, fontweight='bold')
    
    # Data to compare
    params = [
        ('swh_total', 'Total SWH (m)'),
        ('tp', 'Peak Period (s)'),
        ('mean_dir', 'Mean Direction (°)'),
        ('swh_wind_sea', 'Wind Sea SWH (m)'),
        ('swh_swell', 'Swell SWH (m)'),
        ('swell_fraction', 'Swell Fraction')
    ]
    
    for idx, (param, label) in enumerate(params):
        ax = axes[idx // 3, idx % 3]
        
        data_to_plot = []
        labels_to_plot = []
        
        if len(swim_df) > 0 and param in swim_df.columns:
            data_to_plot.append(swim_df[param].values)
            labels_to_plot.append('SWIM')
        
        if len(sar_df) > 0 and param in sar_df.columns:
            data_to_plot.append(sar_df[param].values)
            labels_to_plot.append('SAR')
        
        if data_to_plot:
            bp = ax.boxplot(data_to_plot, labels=labels_to_plot, 
                           patch_artist=True, showmeans=True)
            
            # Color boxes
            colors = ['#1f77b4', '#d62728']
            for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)
        
        ax.set_ylabel(label, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_title(label, fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def main():
    """Run focused Akará analysis."""
    # Get project root
    project_root = Path(__file__).parent.parent
    figures_dir = project_root / 'figures'
    data_dir = project_root / 'data'
    
    print("\n" + "="*60)
    print("FOCUSED ANALYSIS - AKARÁ CYCLONE")
    print("="*60)
    print(f"Region: {AKARA_LON_MIN}°E to {AKARA_LON_MAX}°E, {AKARA_LAT_MIN}°N to {AKARA_LAT_MAX}°N")
    print(f"Period: {AKARA_START} to {AKARA_END}")
    
    # Load analysis results
    print("\n📂 Loading analysis results...")
    swim_results = pd.read_csv(data_dir / 'swim_analysis_results.csv')
    swim_results['datetime'] = pd.to_datetime(swim_results['datetime'])
    
    sar_results = pd.read_csv(data_dir / 'sar_analysis_results.csv')
    sar_results['datetime'] = pd.to_datetime(sar_results['datetime'])
    
    # Filter for Akará region
    print("🔍 Filtering data for Akará region...")
    swim_akara = filter_akara_region(swim_results)
    sar_akara = filter_akara_region(sar_results)
    
    print(f"\n📊 SWIM data in Akará region: {len(swim_akara)} measurements")
    print(f"📊 SAR data in Akará region: {len(sar_akara)} measurements")
    
    if len(swim_akara) > 0:
        print(f"\nSWIM Statistics for Akará:")
        print(f"  SWH range: {swim_akara['swh_total'].min():.2f} - {swim_akara['swh_total'].max():.2f} m")
        print(f"  Mean SWH: {swim_akara['swh_total'].mean():.2f} m")
        print(f"  Peak period range: {swim_akara['tp'].min():.1f} - {swim_akara['tp'].max():.1f} s")
        print(f"  Mean swell fraction: {swim_akara['swell_fraction'].mean()*100:.1f}%")
    
    if len(sar_akara) > 0:
        print(f"\nSAR Statistics for Akará:")
        print(f"  SWH range: {sar_akara['swh_total'].min():.2f} - {sar_akara['swh_total'].max():.2f} m")
        print(f"  Mean SWH: {sar_akara['swh_total'].mean():.2f} m")
        print(f"  Peak period range: {sar_akara['tp'].min():.1f} - {sar_akara['tp'].max():.1f} s")
        print(f"  Mean swell fraction: {sar_akara['swell_fraction'].mean()*100:.1f}%")
    
    # Create comparison plots
    if len(swim_akara) > 0 or len(sar_akara) > 0:
        print("\n📊 Creating comparison plots...")
        plot_akara_comparison(
            swim_akara, 
            sar_akara,
            output_file=figures_dir / 'akara_swim_sar_comparison.png'
        )
        
        plot_akara_statistics(
            swim_akara,
            sar_akara,
            output_file=figures_dir / 'akara_statistics_comparison.png'
        )
        
        # Save filtered data
        if len(swim_akara) > 0:
            swim_akara.to_csv(data_dir / 'swim_akara_region.csv', index=False)
            print(f"💾 Saved SWIM Akará data to: {data_dir / 'swim_akara_region.csv'}")
        
        if len(sar_akara) > 0:
            sar_akara.to_csv(data_dir / 'sar_akara_region.csv', index=False)
            print(f"💾 Saved SAR Akará data to: {data_dir / 'sar_akara_region.csv'}")
        
        print("\n✅ Focused Akará analysis complete!")
    else:
        print("\n⚠️  No data found in Akará region for the specified time period.")
        print("    The satellite spectra data may cover different regions.")


if __name__ == '__main__':
    main()
