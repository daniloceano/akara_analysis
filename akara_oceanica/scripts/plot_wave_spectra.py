"""
Visualize wave spectra and analysis results.

This module creates various plots to explore wave spectra data:
- Polar plots of directional spectra
- Time series of integrated parameters
- Spectral evolution animations
- Comparison between SWIM and SAR
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


def plot_polar_spectrum(spectrum: np.ndarray, frequencies: np.ndarray, 
                        directions: np.ndarray, title: str = '',
                        output_file: str = None, vmax: float = None):
    """
    Plot directional wave spectrum in polar coordinates.
    
    Args:
        spectrum: 2D array (frequency x direction)
        frequencies: Frequency array (Hz)
        directions: Direction array (degrees)
        title: Plot title
        output_file: Optional path to save figure
        vmax: Maximum value for colorscale
    """
    # Convert to polar coordinates
    theta = np.deg2rad(directions)
    r = frequencies
    
    # Create meshgrid
    THETA, R = np.meshgrid(theta, r)
    
    # Create figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='polar')
    
    # Plot spectrum
    if vmax is None:
        vmax = np.percentile(spectrum[spectrum > 0], 95) if np.any(spectrum > 0) else 1.0
    
    c = ax.contourf(THETA, R, spectrum, levels=20, cmap='turbo', vmax=vmax)
    
    # Formatting
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_ylabel('Frequency (Hz)', labelpad=30)
    ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(c, ax=ax, pad=0.1, shrink=0.8)
    cbar.set_label('Spectral Density (m²/Hz/deg)', fontsize=10)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def plot_spectrum_grid(spectra_list: List[Dict], frequencies: np.ndarray,
                       directions: np.ndarray, title: str = '',
                       output_file: str = None, max_plots: int = 9):
    """
    Plot multiple spectra in a grid.
    
    Args:
        spectra_list: List of spectrum dictionaries
        frequencies: Frequency array
        directions: Direction array
        title: Overall title
        output_file: Path to save figure
        max_plots: Maximum number of plots to show
    """
    n_plots = min(len(spectra_list), max_plots)
    ncols = 3
    nrows = int(np.ceil(n_plots / ncols))
    
    fig = plt.figure(figsize=(15, 5 * nrows))
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
    
    # Convert to polar
    theta = np.deg2rad(directions)
    r = frequencies
    THETA, R = np.meshgrid(theta, r)
    
    # Find global vmax
    all_spectra = [s['spectrum'] for s in spectra_list[:n_plots]]
    vmax = np.percentile(np.concatenate([sp.flatten() for sp in all_spectra if np.any(sp > 0)]), 95)
    
    for i, spec_data in enumerate(spectra_list[:n_plots]):
        ax = fig.add_subplot(nrows, ncols, i + 1, projection='polar')
        
        spectrum = spec_data['spectrum']
        
        # Plot
        c = ax.contourf(THETA, R, spectrum, levels=15, cmap='turbo', vmax=vmax)
        
        # Format
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        
        # Title with datetime and location
        dt_str = spec_data['datetime'].strftime('%Y-%m-%d %H:%M')
        loc_str = f"({spec_data['lon']:.1f}°E, {spec_data['lat']:.1f}°N)"
        ax.set_title(f"{dt_str}\n{loc_str}", fontsize=9)
        
        if i % ncols == 0:
            ax.set_ylabel('Freq (Hz)', labelpad=20, fontsize=8)
    
    # Add shared colorbar
    fig.subplots_adjust(right=0.92)
    cbar_ax = fig.add_axes([0.94, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(c, cax=cbar_ax)
    cbar.set_label('Spectral Density (m²/Hz/deg)', fontsize=10)
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def plot_time_series(df: pd.DataFrame, output_file: str = None):
    """
    Plot time series of wave parameters.
    
    Args:
        df: DataFrame with analyzed parameters
        output_file: Path to save figure
    """
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # 1. Significant Wave Height
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['datetime'], df['swh_total'], 'o-', color='#1f77b4', 
             linewidth=2, markersize=6, label='Total SWH')
    ax1.plot(df['datetime'], df['swh_wind_sea'], 's-', color='#ff7f0e', 
             linewidth=1.5, markersize=4, alpha=0.7, label='Wind Sea')
    ax1.plot(df['datetime'], df['swh_swell'], '^-', color='#2ca02c', 
             linewidth=1.5, markersize=4, alpha=0.7, label='Swell')
    ax1.set_ylabel('Significant Wave Height (m)', fontsize=11, fontweight='bold')
    ax1.set_title('Wave Height Evolution', fontsize=12, fontweight='bold')
    ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Peak Period
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(df['datetime'], df['tp'], 'o-', color='#d62728', linewidth=2, markersize=6)
    ax2.set_ylabel('Peak Period (s)', fontsize=11, fontweight='bold')
    ax2.set_title('Peak Period', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Mean Direction
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df['datetime'], df['mean_dir'], 'o-', color='#9467bd', linewidth=2, markersize=6)
    ax3.set_ylabel('Mean Direction (°)', fontsize=11, fontweight='bold')
    ax3.set_title('Wave Direction', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, 360)
    ax3.set_yticks([0, 90, 180, 270, 360])
    ax3.set_yticklabels(['N (0°)', 'E (90°)', 'S (180°)', 'W (270°)', 'N (360°)'])
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Directional Spread
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(df['datetime'], df['dir_spread'], 'o-', color='#8c564b', linewidth=2, markersize=6)
    ax4.set_ylabel('Directional Spread (°)', fontsize=11, fontweight='bold')
    ax4.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax4.set_title('Directional Spread', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 5. Swell Fraction
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(df['datetime'], df['swell_fraction'] * 100, 'o-', color='#e377c2', 
             linewidth=2, markersize=6)
    ax5.set_ylabel('Swell Fraction (%)', fontsize=11, fontweight='bold')
    ax5.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax5.set_title('Swell Dominance', fontsize=12, fontweight='bold')
    ax5.set_ylim(0, 100)
    ax5.grid(True, alpha=0.3, linestyle='--')
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def plot_spatial_distribution(df: pd.DataFrame, output_file: str = None):
    """
    Plot spatial distribution of measurements with wave parameters.
    
    Args:
        df: DataFrame with analyzed parameters
        output_file: Path to save figure
    """
    fig = plt.figure(figsize=(15, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.25, wspace=0.25)
    
    # Define extent
    lon_min, lon_max = df['lon'].min() - 5, df['lon'].max() + 5
    lat_min, lat_max = df['lat'].min() - 5, df['lat'].max() + 5
    
    # 1. SWH
    ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree())
    ax1.coastlines(resolution='10m', linewidth=0.8)
    ax1.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax1.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.1)
    ax1.gridlines(draw_labels=True, alpha=0.3)
    ax1.set_extent([lon_min, lon_max, lat_min, lat_max])
    
    sc1 = ax1.scatter(df['lon'], df['lat'], c=df['swh_total'], 
                      s=100, cmap='turbo', vmin=0, vmax=df['swh_total'].max(),
                      edgecolors='black', linewidths=0.5, alpha=0.8,
                      transform=ccrs.PlateCarree())
    ax1.set_title('Significant Wave Height (m)', fontsize=12, fontweight='bold')
    cbar1 = plt.colorbar(sc1, ax=ax1, shrink=0.7)
    cbar1.set_label('SWH (m)', fontsize=10)
    
    # 2. Peak Period
    ax2 = fig.add_subplot(gs[0, 1], projection=ccrs.PlateCarree())
    ax2.coastlines(resolution='10m', linewidth=0.8)
    ax2.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax2.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.1)
    ax2.gridlines(draw_labels=True, alpha=0.3)
    ax2.set_extent([lon_min, lon_max, lat_min, lat_max])
    
    sc2 = ax2.scatter(df['lon'], df['lat'], c=df['tp'], 
                      s=100, cmap='viridis', vmin=df['tp'].min(), vmax=df['tp'].max(),
                      edgecolors='black', linewidths=0.5, alpha=0.8,
                      transform=ccrs.PlateCarree())
    ax2.set_title('Peak Period (s)', fontsize=12, fontweight='bold')
    cbar2 = plt.colorbar(sc2, ax=ax2, shrink=0.7)
    cbar2.set_label('Tp (s)', fontsize=10)
    
    # 3. Mean Direction (using quiver)
    ax3 = fig.add_subplot(gs[1, 0], projection=ccrs.PlateCarree())
    ax3.coastlines(resolution='10m', linewidth=0.8)
    ax3.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax3.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.1)
    ax3.gridlines(draw_labels=True, alpha=0.3)
    ax3.set_extent([lon_min, lon_max, lat_min, lat_max])
    
    # Convert direction to u, v components
    u = np.sin(np.deg2rad(df['mean_dir']))
    v = np.cos(np.deg2rad(df['mean_dir']))
    
    # Color by SWH
    sc3 = ax3.scatter(df['lon'], df['lat'], c=df['swh_total'], 
                      s=100, cmap='turbo', vmin=0, vmax=df['swh_total'].max(),
                      edgecolors='black', linewidths=0.5, alpha=0.6,
                      transform=ccrs.PlateCarree())
    
    # Add direction arrows
    ax3.quiver(df['lon'], df['lat'], u, v, 
               scale=20, width=0.003, headwidth=4, headlength=5,
               color='black', alpha=0.8, transform=ccrs.PlateCarree())
    
    ax3.set_title('Mean Wave Direction', fontsize=12, fontweight='bold')
    cbar3 = plt.colorbar(sc3, ax=ax3, shrink=0.7)
    cbar3.set_label('SWH (m)', fontsize=10)
    
    # 4. Swell Fraction
    ax4 = fig.add_subplot(gs[1, 1], projection=ccrs.PlateCarree())
    ax4.coastlines(resolution='10m', linewidth=0.8)
    ax4.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax4.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.1)
    ax4.gridlines(draw_labels=True, alpha=0.3)
    ax4.set_extent([lon_min, lon_max, lat_min, lat_max])
    
    sc4 = ax4.scatter(df['lon'], df['lat'], c=df['swell_fraction'] * 100, 
                      s=100, cmap='RdYlGn', vmin=0, vmax=100,
                      edgecolors='black', linewidths=0.5, alpha=0.8,
                      transform=ccrs.PlateCarree())
    ax4.set_title('Swell Fraction (%)', fontsize=12, fontweight='bold')
    cbar4 = plt.colorbar(sc4, ax=ax4, shrink=0.7)
    cbar4.set_label('Swell %', fontsize=10)
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"💾 Saved: {output_file}")
    
    plt.close()


def main():
    """Create all visualizations."""
    import sys
    
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
    except ModuleNotFoundError:
        from analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser
        from analyze_wave_spectra import analyze_swim_data, analyze_sar_data
    
    figures_dir = project_root / 'figures'
    figures_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("VISUALIZING WAVE SPECTRA ANALYSIS")
    print("="*60)
    
    # Load and analyze SWIM data
    print("\n🌊 Processing SWIM data...")
    swim_file = project_root / 'data' / 'wave_spectra' / 'SWI_WV1'
    swim_parser = SwimSpectraParser(swim_file)
    swim_spectra = swim_parser.parse_file()
    swim_results = analyze_swim_data(swim_spectra)
    
    frequencies = swim_parser.frequencies
    directions = swim_parser.directions
    
    # Plot SWIM grid
    print("📊 Creating SWIM spectral grid...")
    plot_spectrum_grid(
        swim_spectra[:9], 
        frequencies, 
        directions,
        title='CFOSAT SWIM Wave Spectra - Akará Cyclone',
        output_file=figures_dir / 'swim_spectra_grid.png'
    )
    
    # Plot SWIM time series
    print("📈 Creating SWIM time series...")
    plot_time_series(
        swim_results,
        output_file=figures_dir / 'swim_time_series.png'
    )
    
    # Plot SWIM spatial distribution
    print("🗺️ Creating SWIM spatial distribution...")
    plot_spatial_distribution(
        swim_results,
        output_file=figures_dir / 'swim_spatial_distribution.png'
    )
    
    # Load and analyze SAR data
    print("\n🛰️ Processing SAR data...")
    sar_dir = project_root / 'data' / 'wave_spectra' / 'SENT1'
    sar_parser = SarSpectraParser(sar_dir)
    sar_spectra = sar_parser.parse_all_files()
    sar_results = analyze_sar_data(sar_spectra)
    
    if len(sar_spectra) > 0:
        # Plot SAR grid
        print("📊 Creating SAR spectral grid...")
        plot_spectrum_grid(
            sar_spectra[:9], 
            frequencies, 
            directions,
            title='Sentinel-1A SAR Wave Spectra - Akará Cyclone',
            output_file=figures_dir / 'sar_spectra_grid.png'
        )
        
        # Plot SAR time series
        print("📈 Creating SAR time series...")
        plot_time_series(
            sar_results,
            output_file=figures_dir / 'sar_time_series.png'
        )
        
        # Plot SAR spatial distribution
        print("🗺️ Creating SAR spatial distribution...")
        plot_spatial_distribution(
            sar_results,
            output_file=figures_dir / 'sar_spatial_distribution.png'
        )
    
    print("\n✅ All visualizations complete!")
    print(f"📁 Figures saved to: {figures_dir}")


if __name__ == '__main__':
    main()
