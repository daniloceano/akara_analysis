#!/usr/bin/env python3
"""
Create wave spectra animations combining:
- ERA5 wave height fields (background)
- Satellite directional wave spectra as polar plots (overlay)

Generates animation with all satellite spectra combined.
Plots 1 in every 5 spectra from same track to avoid overlap.

Author: GitHub Copilot + Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cmocean
from pathlib import Path
from datetime import datetime, timedelta
import warnings
import logging
import sys

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))
from analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SpectraAnimator:
    """Class to create wave spectra animations with ERA5 background."""
    
    def __init__(self, era5_file, spectra_dir, output_dir, region=None):
        """
        Initialize the animator.
        
        Args:
            era5_file: ERA5 NetCDF file
            spectra_dir: Directory with wave spectra data
            output_dir: Directory to save animations
            region: Dictionary with bounds {west, east, south, north}
        """
        self.era5_file = PROJECT_ROOT / era5_file
        self.spectra_dir = PROJECT_ROOT / spectra_dir
        self.output_dir = PROJECT_ROOT / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default region (Akará - zoomed to system)
        if region is None:
            self.region = {
                'west': -50.0,
                'east': -30.0,
                'south': -37.0,
                'north': -22.0
            }
        else:
            self.region = region
        
        logger.info(f"📁 ERA5 data: {self.era5_file}")
        logger.info(f"📁 Spectra data: {self.spectra_dir}")
        logger.info(f"🎬 Animations: {self.output_dir}")
        logger.info(f"🌍 Region: {self.region}")
        
        # Configure style
        self.setup_plotting_style()
        
        # Load data
        self.load_era5_data()
        self.load_spectra_data()
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
    
    def load_spectra_data(self):
        """Load wave spectra from SWIM and SAR."""
        logger.info("📡 Loading wave spectra...")
        
        self.all_spectra = []
        
        # Load SWIM spectra
        swim_file = self.spectra_dir / 'SWI_WV1'
        if swim_file.exists():
            logger.info("  Loading CFOSAT SWIM spectra...")
            try:
                parser = SwimSpectraParser(swim_file)
                swim_spectra = parser.parse_file()
                
                # Add source tag and UTC timestamps
                for spec in swim_spectra:
                    spec['source'] = 'SWIM'
                    # Localize to UTC if needed
                    if spec['datetime'].tz is None:
                        spec['datetime'] = spec['datetime'].tz_localize('UTC')
                    else:
                        spec['datetime'] = spec['datetime'].tz_convert('UTC')
                
                self.all_spectra.extend(swim_spectra)
                logger.info(f"  ✅ SWIM: {len(swim_spectra)} spectra")
            except Exception as e:
                logger.warning(f"  ⚠️ Error loading SWIM: {e}")
        
        # Load SAR spectra
        sar_dir = self.spectra_dir / 'SENT1'
        if sar_dir.exists() and sar_dir.is_dir():
            logger.info("  Loading Sentinel-1A SAR spectra...")
            try:
                parser = SarSpectraParser(sar_dir)
                sar_files = sorted(sar_dir.glob('SAR*'))
                
                sar_count = 0
                for sar_file in sar_files:
                    try:
                        sar_spectra = parser.parse_file(sar_file)
                        
                        # Add source tag and UTC timestamps
                        for spec in sar_spectra:
                            spec['source'] = 'SAR'
                            if spec['datetime'].tz is None:
                                spec['datetime'] = spec['datetime'].tz_localize('UTC')
                            else:
                                spec['datetime'] = spec['datetime'].tz_convert('UTC')
                        
                        self.all_spectra.extend(sar_spectra)
                        sar_count += len(sar_spectra)
                    except Exception as e:
                        logger.warning(f"  ⚠️ Error in {sar_file.name}: {e}")
                
                logger.info(f"  ✅ SAR: {sar_count} spectra from {len(sar_files)} files")
            except Exception as e:
                logger.warning(f"  ⚠️ Error loading SAR: {e}")
        
        # Convert longitudes from 0-360 to -180-180 if needed
        for spec in self.all_spectra:
            if spec['lon'] > 180:
                spec['lon'] -= 360
        
        # Sort by time
        self.all_spectra.sort(key=lambda x: x['datetime'])
        
        # Filter to region
        self.all_spectra = [
            s for s in self.all_spectra
            if (self.region['west'] <= s['lon'] <= self.region['east'] and
                self.region['south'] <= s['lat'] <= self.region['north'])
        ]
        
        logger.info(f"📊 Total spectra in region: {len(self.all_spectra)}")
        
        # Check temporal distribution
        if self.all_spectra:
            import pandas as pd
            times = [s['datetime'] for s in self.all_spectra]
            dates = pd.Series(times).dt.date.value_counts().sort_index()
            logger.info("  Temporal distribution:")
            for date, count in dates.items():
                logger.info(f"    {date}: {count} spectra")
        
        # Apply 1-in-3 sampling per track (less aggressive to keep more data)
        self.sample_spectra_by_track(sample_rate=3)
    
    def sample_spectra_by_track(self, sample_rate=3):
        """
        Sample 1 in every N spectra from same track to avoid overlap.
        
        Args:
            sample_rate: Keep 1 in every sample_rate points
        """
        logger.info(f"  Sampling 1 in {sample_rate} spectra per track...")
        
        # Group by source and date (approximation of "track")
        from collections import defaultdict
        tracks = defaultdict(list)
        
        for spec in self.all_spectra:
            # Create track key: source + date
            date_key = spec['datetime'].strftime('%Y%m%d')
            track_key = f"{spec['source']}_{date_key}"
            tracks[track_key].append(spec)
        
        # Sample each track
        sampled = []
        for track_key, track_spectra in tracks.items():
            # Sort by time within track
            track_spectra.sort(key=lambda x: x['datetime'])
            # Keep every Nth spectrum
            sampled.extend(track_spectra[::sample_rate])
        
        original_count = len(self.all_spectra)
        self.all_spectra = sampled
        logger.info(f"  ✅ Reduced from {original_count} to {len(self.all_spectra)} spectra")
    
    def create_time_bins(self):
        """Create hourly time bins from ERA5."""
        logger.info("⏰ Creating time bins...")
        
        # Get ERA5 time range and ensure UTC timezone
        self.time_bins = pd.to_datetime(self.era5_ds.time.values)
        try:
            if self.time_bins.tz is None:
                self.time_bins = self.time_bins.tz_localize('UTC')
            else:
                self.time_bins = self.time_bins.tz_convert('UTC')
        except Exception:
            self.time_bins = pd.DatetimeIndex([
                pd.to_datetime(t).tz_localize('UTC') if pd.to_datetime(t).tzinfo is None 
                else pd.to_datetime(t).tz_convert('UTC') 
                for t in self.time_bins
            ])
        
        logger.info(f"📅 Period: {self.time_bins[0]} to {self.time_bins[-1]}")
        logger.info(f"⏱️ Total frames: {len(self.time_bins)}")
    
    def get_spectra_for_time(self, time_center, window_hours=6):
        """
        Get spectra within a time window.
        
        Args:
            time_center: Central timestamp
            window_hours: Time window in hours (±window_hours)
            
        Returns:
            List of spectra dictionaries
        """
        time_start = time_center - pd.Timedelta(hours=window_hours)
        time_end = time_center + pd.Timedelta(hours=window_hours)
        
        spectra_in_window = [
            s for s in self.all_spectra
            if time_start <= s['datetime'] <= time_end
        ]
        
        return spectra_in_window
    
    def plot_polar_spectrum(self, ax, lon, lat, spectrum, frequencies, directions, 
                           size=1.5, transform=None):
        """
        Plot a single directional spectrum as a polar plot (frequency-direction).
        
        Args:
            ax: Cartopy axis (main map)
            lon, lat: Position to plot spectrum
            spectrum: 2D array (frequencies x directions)
            frequencies: Frequency array
            directions: Direction array (degrees)
            size: Size scaling factor (degrees)
            transform: Coordinate transform for positioning
        """
        # Convert directions to radians (oceanographic convention)
        # North = 0°, East = 90°, etc. (direction waves are coming FROM)
        theta = np.radians(directions)
        
        # Create meshgrid for polar plot
        # Radius = frequency (normalized to 0-1 for plotting)
        freq_norm = (frequencies - frequencies.min()) / (frequencies.max() - frequencies.min())
        
        THETA, R = np.meshgrid(theta, freq_norm)
        
        # Calculate Hs from spectrum for each frequency-direction bin
        # Hs ≈ 4 * sqrt(E * df * dtheta) where E is energy density
        # For visualization, we'll use sqrt of energy to approximate wave height contribution
        df = np.diff(frequencies).mean() if len(frequencies) > 1 else 0.01
        dtheta = np.radians(360 / len(directions))
        
        # Energy to wave height conversion (simplified)
        # Using Hs = 4 * sqrt(m0) where m0 is the spectral moment
        hs_contrib = 4 * np.sqrt(spectrum * df * dtheta)
        
        # Normalize for color mapping (0-max Hs)
        hs_max = 3.0  # Maximum Hs for color scale
        hs_norm = np.clip(hs_contrib / hs_max, 0, 1)
        
        # Create small polar plot at this location
        # Convert polar coordinates to cartesian offsets
        # Rotate by 90° to have North at top (standard oceanographic convention)
        angle_offset = np.pi / 2  # 90° rotation
        X_offset = R * size * np.sin(THETA + angle_offset)
        Y_offset = R * size * np.cos(THETA + angle_offset)
        
        # Plot as colored cells
        n_freq = len(frequencies)
        n_dir = len(directions)
        
        # Use pcolormesh approach - plot each cell
        for i in range(n_freq - 1):
            for j in range(n_dir):
                # Get corners of this cell
                j_next = (j + 1) % n_dir
                
                r1, r2 = freq_norm[i], freq_norm[i + 1]
                th1, th2 = theta[j], theta[j_next]
                
                # Create quadrilateral vertices
                corners_r = [r1, r2, r2, r1]
                corners_th = [th1, th1, th2, th2]
                
                # Convert to cartesian
                x_corners = [lon + r * size * np.sin(t + angle_offset) 
                            for r, t in zip(corners_r, corners_th)]
                y_corners = [lat + r * size * np.cos(t + angle_offset) 
                            for r, t in zip(corners_r, corners_th)]
                
                # Get color value for this cell
                hs_val = hs_contrib[i, j]
                
                if hs_val > 0.01:  # Only plot cells with significant wave height
                    # Map to turbo colormap
                    color_val = hs_norm[i, j]
                    color = plt.cm.turbo(color_val)
                    
                    # Create polygon
                    verts = list(zip(x_corners, y_corners))
                    polygon = mpatches.Polygon(
                        verts,
                        closed=True,
                        facecolor=color,
                        edgecolor='none',
                        alpha=0.7,
                        transform=transform if transform else ccrs.PlateCarree(),
                        zorder=10
                    )
                    ax.add_patch(polygon)
        
        # Add center marker (white dot)
        ax.plot(lon, lat, 'wo', markersize=2, transform=ccrs.PlateCarree(), 
               zorder=11, alpha=0.9, markeredgecolor='black', markeredgewidth=0.5)
    
    def create_single_frame(self, ax, time_idx):
        """
        Create a single animation frame.
        
        Args:
            ax: Matplotlib axis
            time_idx: Time index
        """
        ax.clear()
        
        # Get current time
        current_time = self.time_bins[time_idx]
        
        # Plot ERA5 background field
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
        
        # Get spectra for this time window
        spectra = self.get_spectra_for_time(current_time, window_hours=3)
        
        # Plot each spectrum as polar plot
        if spectra:
            logger.info(f"  Frame {time_idx+1}: Plotting {len(spectra)} spectra")
            
            # Get frequency and direction arrays (same for SWIM and SAR)
            frequencies = np.array([0.0345 * (1.1 ** i) for i in range(30)])
            directions = np.arange(7.5, 360, 15)
            
            for spec in spectra:
                self.plot_polar_spectrum(
                    ax,
                    spec['lon'],
                    spec['lat'],
                    spec['spectrum'],
                    frequencies,
                    directions,
                    size=1.5,  # Size adjusted for zoomed region
                    transform=ccrs.PlateCarree()
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
        ax.set_title(
            f'Wave Height (ERA5) + Directional Spectra (Satellites)\n{current_time.strftime("%Y-%m-%d %H:%M UTC")}',
            fontsize=14,
            fontweight='bold',
            color='white',
            pad=10
        )
        
        # Add legend/info box for spectra
        info_text = (
            'Directional Spectra:\n'
            '• Radius = Frequency\n'
            '• Angle = Direction\n'
            '• Color = Hs contribution'
        )
        ax.text(
            0.02, 0.98, info_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7, edgecolor='white'),
            color='white'
        )
        
        return ax
    
    def create_animation(self, fps=2, interval=500):
        """
        Create complete animation.
        
        Args:
            fps: Frames per second
            interval: Interval between frames (ms)
        """
        logger.info("🎬 Creating spectra animation...")
        
        # Create figure
        fig = plt.figure(figsize=(18, 12), facecolor='black')
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Create animation
        def update_frame(frame_idx):
            logger.info(f"  Frame {frame_idx+1}/{len(self.time_bins)}")
            return self.create_single_frame(ax, frame_idx)
        
        anim = animation.FuncAnimation(
            fig,
            update_frame,
            frames=len(self.time_bins),
            interval=interval,
            blit=False,
            repeat=True
        )
        
        # Save
        output_file = self.output_dir / 'wave_spectra_animation.mp4'
        logger.info(f"💾 Saving animation: {output_file}")
        
        # Configure ffmpeg
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            plt.rcParams['animation.ffmpeg_path'] = ffmpeg_path
            logger.info(f"  Using imageio-ffmpeg: {ffmpeg_path}")
        except ImportError:
            logger.warning("  imageio-ffmpeg not found, using system ffmpeg")
        
        writer = animation.FFMpegWriter(
            fps=fps, 
            bitrate=3000,  # Higher bitrate for better quality with complex plots
            codec='libx264',
            extra_args=['-pix_fmt', 'yuv420p']
        )
        
        anim.save(output_file, writer=writer)
        plt.close(fig)
        
        logger.info(f"✅ Animation saved: {output_file}")
        
        return output_file


def main():
    """Main function."""
    logger.info("=" * 70)
    logger.info("🎬 DIRECTIONAL SPECTRA ANIMATION - ERA5 + SATELLITES 🌊")
    logger.info("=" * 70)
    logger.info("")
    
    # Configure paths
    era5_file = 'data/era5_waves/era5_waves_akara_20240214_20240222.nc'
    spectra_dir = 'data/wave_spectra'
    output_dir = 'figures/animations'
    
    # Check if ERA5 exists
    era5_path = PROJECT_ROOT / era5_file
    if not era5_path.exists():
        logger.error(f"❌ ERA5 file not found: {era5_path}")
        logger.info("💡 Available ERA5 files:")
        era5_dir = PROJECT_ROOT / 'data/era5_waves'
        if era5_dir.exists():
            for f in era5_dir.glob('*.nc'):
                logger.info(f"   - {f.name}")
        return
    
    # Check if spectra data exists
    spectra_path = PROJECT_ROOT / spectra_dir
    if not spectra_path.exists():
        logger.error(f"❌ Spectra directory not found: {spectra_path}")
        return
    
    # Create animator
    animator = SpectraAnimator(era5_file, spectra_dir, output_dir)
    
    # Create animation
    logger.info("")
    animator.create_animation(fps=2, interval=500)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎉 SPECTRA ANIMATION COMPLETE! 🚀")
    logger.info("=" * 70)
    logger.info(f"📁 Saved in: {animator.output_dir}")
    logger.info("")
    logger.info("💡 The animation shows:")
    logger.info("   - ERA5 wave height field (background)")
    logger.info("   - Directional wave spectra as polar plots (overlay)")
    logger.info("   - Frequency-direction structure with Hs contribution")
    logger.info("   - Region: 22°S-37°S, 30°W-50°W (zoomed to system)")
    logger.info(f"   - Time window: ±6 hours for satellite data")
    logger.info(f"   - Sampling: 1 in 3 spectra per track")


if __name__ == "__main__":
    main()
