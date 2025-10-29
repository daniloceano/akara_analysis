#!/usr/bin/env python3
"""
Criar visualizações combinadas SWOT + ERA5 no estilo SWOT original
- Snapshots para todos os períodos
- GIF animado
- Série temporal para ponto próximo do Rio de Janeiro
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator
import warnings
warnings.filterwarnings('ignore')

class CombinedSWOTxERA5Visualizer:
    def __init__(self, swot_file, era5_file, output_dir):
        """
        Initialize the visualizer with data files
        """
        self.swot_file = swot_file
        self.era5_file = era5_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and process data
        print("📂 Carregando dados...")
        self.swot_data = xr.open_dataset(swot_file)
        era5_raw = xr.open_dataset(era5_file)
        
        # Process ERA5 data - average over ensemble members if present
        if 'number' in era5_raw.dims:
            self.era5_data = era5_raw.mean('number')
        else:
            self.era5_data = era5_raw
            
        # Remove expver dimension if present
        if 'expver' in self.era5_data.dims:
            self.era5_data = self.era5_data.isel(expver=0)
        
        print(f"✅ SWOT: {len(self.swot_data.time)} pontos temporais")
        print(f"✅ ERA5: {len(self.era5_data.valid_time)} pontos temporais")
        
        # Setup Rio coordinates
        self.rio_lat = -22.9068
        self.rio_lon = -43.1729
        
        # Find Rio indices in SWOT data
        self.rio_lat_idx = np.argmin(np.abs(self.swot_data.latitude.values - self.rio_lat))
        self.rio_lon_idx = np.argmin(np.abs(self.swot_data.longitude.values - self.rio_lon))
        
    def interpolate_era5_to_swot_grid(self, era5_data, swot_lats, swot_lons):
        """
        Interpolate ERA5 data to SWOT grid
        """
        # Get ERA5 coordinates
        era5_lats = era5_data.latitude.values
        era5_lons = era5_data.longitude.values
        
        # Create meshgrids
        era5_lon_grid, era5_lat_grid = np.meshgrid(era5_lons, era5_lats)
        swot_lon_grid, swot_lat_grid = np.meshgrid(swot_lons, swot_lats)
        
        # Interpolate each variable
        interpolated = {}
        for var in ['swh', 'mwd', 'mwp', 'pp1d']:
            if var in era5_data:
                # Get the data
                data = era5_data[var].values
                
                # Create interpolator
                interpolator = RegularGridInterpolator(
                    (era5_lats, era5_lons), 
                    data,
                    method='linear',
                    bounds_error=False,
                    fill_value=np.nan
                )
                
                # Interpolate to SWOT grid
                points = np.stack([swot_lat_grid.ravel(), swot_lon_grid.ravel()], axis=-1)
                interpolated_data = interpolator(points).reshape(swot_lat_grid.shape)
                interpolated[var] = interpolated_data
                
        return interpolated
        
    def find_closest_era5_time(self, swot_time):
        """
        Find closest ERA5 time to SWOT time
        """
        swot_time_pd = pd.to_datetime(swot_time.values)
        era5_times_pd = pd.to_datetime(self.era5_data.valid_time.values)
        
        time_diffs = np.abs(era5_times_pd - swot_time_pd)
        closest_idx = np.argmin(time_diffs)
        
        return closest_idx, era5_times_pd[closest_idx]
        
    def create_snapshot(self, time_idx, save_path=None):
        """
        Create a single snapshot combining SWOT and ERA5 data
        """
        # Get SWOT data for this time
        swot_time = self.swot_data.time[time_idx]
        ssh_data = self.swot_data.ssh_karin[time_idx].values
        
        # Find closest ERA5 time and data
        era5_idx, era5_time = self.find_closest_era5_time(swot_time)
        era5_subset = self.era5_data.isel(valid_time=era5_idx)
        
        # Interpolate ERA5 to SWOT grid
        era5_interp = self.interpolate_era5_to_swot_grid(
            era5_subset, 
            self.swot_data.latitude.values,
            self.swot_data.longitude.values
        )
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 12))
        
        # Common projection and extent
        proj = ccrs.PlateCarree()
        extent = [
            self.swot_data.longitude.min(), self.swot_data.longitude.max(),
            self.swot_data.latitude.min(), self.swot_data.latitude.max()
        ]
        
        # 1. SSH SWOT
        ax1 = plt.subplot(2, 3, 1, projection=proj)
        ax1.set_extent(extent, crs=proj)
        ax1.add_feature(cfeature.COASTLINE)
        ax1.add_feature(cfeature.BORDERS)
        ax1.gridlines(draw_labels=True, alpha=0.3)
        
        im1 = ax1.pcolormesh(
            self.swot_data.longitude, self.swot_data.latitude, ssh_data,
            cmap='RdYlBu_r', transform=proj, shading='auto'
        )
        ax1.set_title('SSH SWOT (m)')
        plt.colorbar(im1, ax=ax1, shrink=0.8)
        
        # Mark Rio
        ax1.plot(self.rio_lon, self.rio_lat, 'r*', markersize=15, transform=proj)
        
        # 2. Significant Wave Height
        if 'swh' in era5_interp:
            ax2 = plt.subplot(2, 3, 2, projection=proj)
            ax2.set_extent(extent, crs=proj)
            ax2.add_feature(cfeature.COASTLINE)
            ax2.add_feature(cfeature.BORDERS)
            ax2.gridlines(draw_labels=True, alpha=0.3)
            
            im2 = ax2.pcolormesh(
                self.swot_data.longitude, self.swot_data.latitude, era5_interp['swh'],
                cmap='viridis', transform=proj, shading='auto'
            )
            ax2.set_title('Significant Wave Height (m)')
            plt.colorbar(im2, ax=ax2, shrink=0.8)
            ax2.plot(self.rio_lon, self.rio_lat, 'r*', markersize=15, transform=proj)
        
        # 3. Wave Period
        if 'mwp' in era5_interp:
            ax3 = plt.subplot(2, 3, 3, projection=proj)
            ax3.set_extent(extent, crs=proj)
            ax3.add_feature(cfeature.COASTLINE)
            ax3.add_feature(cfeature.BORDERS)
            ax3.gridlines(draw_labels=True, alpha=0.3)
            
            im3 = ax3.pcolormesh(
                self.swot_data.longitude, self.swot_data.latitude, era5_interp['mwp'],
                cmap='plasma', transform=proj, shading='auto'
            )
            ax3.set_title('Mean Wave Period (s)')
            plt.colorbar(im3, ax=ax3, shrink=0.8)
            ax3.plot(self.rio_lon, self.rio_lat, 'r*', markersize=15, transform=proj)
        
        # 4. Combined analysis - SSH vs SWH
        if 'swh' in era5_interp:
            ax4 = plt.subplot(2, 3, 4)
            
            # Flatten arrays and remove NaN
            ssh_flat = ssh_data.flatten()
            swh_flat = era5_interp['swh'].flatten()
            
            valid_mask = ~(np.isnan(ssh_flat) | np.isnan(swh_flat))
            ssh_valid = ssh_flat[valid_mask]
            swh_valid = swh_flat[valid_mask]
            
            if len(ssh_valid) > 0:
                ax4.scatter(ssh_valid, swh_valid, alpha=0.5, s=1)
                ax4.set_xlabel('SSH SWOT (m)')
                ax4.set_ylabel('SWH ERA5 (m)')
                ax4.set_title('SSH vs Wave Height')
                ax4.grid(True, alpha=0.3)
                
                # Add correlation
                if len(ssh_valid) > 1:
                    corr = np.corrcoef(ssh_valid, swh_valid)[0, 1]
                    ax4.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax4.transAxes, 
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 5. Rio timeseries preview
        ax5 = plt.subplot(2, 3, 5)
        
        # Get all times up to current
        times_pd = pd.to_datetime(self.swot_data.time[:time_idx+1].values)
        ssh_rio = self.swot_data.ssh_karin[:time_idx+1, self.rio_lat_idx, self.rio_lon_idx].values
        
        ax5.plot(times_pd, ssh_rio, 'b-o', linewidth=2, markersize=4, label='SSH SWOT')
        ax5.axvline(pd.to_datetime(swot_time.values), color='red', linestyle='--', alpha=0.7, label='Current time')
        ax5.set_ylabel('SSH (m)')
        ax5.set_title(f'Rio de Janeiro - SSH Evolution')
        ax5.grid(True, alpha=0.3)
        ax5.legend()
        
        # Format x-axis
        ax5.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax5.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45)
        
        # 6. Location map
        ax6 = plt.subplot(2, 3, 6, projection=proj)
        ax6.set_extent(extent, crs=proj)
        ax6.add_feature(cfeature.COASTLINE)
        ax6.add_feature(cfeature.BORDERS)
        ax6.add_feature(cfeature.LAND, alpha=0.3)
        ax6.add_feature(cfeature.OCEAN, alpha=0.3)
        ax6.gridlines(draw_labels=True, alpha=0.3)
        
        # Highlight Rio
        ax6.plot(self.rio_lon, self.rio_lat, 'r*', markersize=20, transform=proj, label='Rio de Janeiro')
        ax6.set_title('Study Area')
        ax6.legend()
        
        # Main title
        time_str = pd.to_datetime(swot_time.values).strftime('%Y-%m-%d %H:%M')
        era5_time_str = era5_time.strftime('%Y-%m-%d %H:%M')
        fig.suptitle(f'SWOT + ERA5 Combined Analysis\\nSWOT: {time_str} | ERA5: {era5_time_str}', 
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Snapshot salvo: {save_path}")
        
        return fig
        
    def create_all_snapshots(self):
        """
        Create snapshots for all time periods
        """
        print("\\n📸 Criando snapshots para todos os períodos...")
        
        snapshot_dir = self.output_dir / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        
        snapshot_files = []
        
        for i in range(len(self.swot_data.time)):
            time_str = pd.to_datetime(self.swot_data.time[i].values).strftime('%Y%m%d_%H%M%S')
            save_path = snapshot_dir / f"combined_snapshot_{i:02d}_{time_str}.png"
            
            try:
                fig = self.create_snapshot(i, save_path)
                plt.close(fig)
                snapshot_files.append(save_path)
                
            except Exception as e:
                print(f"❌ Erro no snapshot {i}: {e}")
                continue
                
        print(f"✅ {len(snapshot_files)} snapshots criados em {snapshot_dir}")
        return snapshot_files
        
    def create_animated_gif(self, fps=2):
        """
        Create animated GIF from snapshots
        """
        print("\\n🎬 Criando GIF animado...")
        
        try:
            # Create temporary snapshots for animation
            temp_figs = []
            for i in range(len(self.swot_data.time)):
                fig = self.create_snapshot(i)
                temp_figs.append(fig)
            
            # Create animation
            def animate(frame):
                return temp_figs[frame]
            
            if temp_figs:
                # Save as GIF
                gif_path = self.output_dir / "combined_animation.gif"
                
                # Use first figure to set up animation
                fig = temp_figs[0]
                anim = FuncAnimation(fig, animate, frames=len(temp_figs), interval=1000/fps, repeat=True)
                anim.save(gif_path, writer='pillow', fps=fps, dpi=100)
                
                # Clean up
                for fig in temp_figs:
                    plt.close(fig)
                    
                print(f"✅ GIF criado: {gif_path}")
                return gif_path
                
        except Exception as e:
            print(f"❌ Erro ao criar GIF: {e}")
            return None
            
    def create_rio_timeseries(self):
        """
        Create Rio de Janeiro timeseries with map inset
        """
        print("\\n📊 Criando série temporal para Rio de Janeiro...")
        
        try:
            fig = plt.figure(figsize=(16, 10))
            
            # Main timeseries plot
            ax_main = plt.subplot(2, 1, 1)
            
            # Get Rio timeseries
            times_pd = pd.to_datetime(self.swot_data.time.values)
            ssh_rio = self.swot_data.ssh_karin[:, self.rio_lat_idx, self.rio_lon_idx].values
            
            # Plot SSH
            ax_main.plot(times_pd, ssh_rio, 'b-o', linewidth=2, markersize=6, label='SSH SWOT')
            ax_main.set_ylabel('SSH (m)', fontsize=12)
            ax_main.set_title('Série Temporal - Rio de Janeiro\\nAltura da Superfície do Mar (SWOT)', fontsize=14, fontweight='bold')
            ax_main.grid(True, alpha=0.3)
            ax_main.legend(fontsize=11)
            
            # Format x-axis
            ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax_main.xaxis.set_major_locator(mdates.DayLocator())
            plt.setp(ax_main.xaxis.get_majorticklabels(), rotation=45)
            
            # Statistics
            ssh_mean = np.nanmean(ssh_rio)
            ssh_std = np.nanstd(ssh_rio)
            ssh_min = np.nanmin(ssh_rio)
            ssh_max = np.nanmax(ssh_rio)
            
            # Add horizontal reference lines
            ax_main.axhline(ssh_mean, color='red', linestyle='--', alpha=0.7, label=f'Média: {ssh_mean:.3f} m')
            ax_main.axhline(ssh_mean + ssh_std, color='orange', linestyle=':', alpha=0.7, label=f'±1σ: {ssh_std:.3f} m')
            ax_main.axhline(ssh_mean - ssh_std, color='orange', linestyle=':', alpha=0.7)
            ax_main.legend(fontsize=10)
            
            # Map with location
            ax_map = plt.subplot(2, 1, 2, projection=ccrs.PlateCarree())
            
            extent = [
                self.swot_data.longitude.min(), self.swot_data.longitude.max(),
                self.swot_data.latitude.min(), self.swot_data.latitude.max()
            ]
            ax_map.set_extent(extent, crs=ccrs.PlateCarree())
            
            # Add features
            ax_map.add_feature(cfeature.COASTLINE, linewidth=0.8)
            ax_map.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax_map.add_feature(cfeature.LAND, alpha=0.3)
            ax_map.add_feature(cfeature.OCEAN, alpha=0.3)
            ax_map.gridlines(draw_labels=True, alpha=0.3)
            
            # Plot mean SSH field
            ssh_mean_field = np.nanmean(self.swot_data.ssh_karin.values, axis=0)
            im = ax_map.pcolormesh(
                self.swot_data.longitude, self.swot_data.latitude, ssh_mean_field,
                cmap='RdYlBu_r', transform=ccrs.PlateCarree(), shading='auto', alpha=0.8
            )
            
            # Highlight Rio
            ax_map.plot(self.rio_lon, self.rio_lat, 'r*', markersize=20, transform=ccrs.PlateCarree(), 
                       label='Rio de Janeiro', markeredgecolor='black', markeredgewidth=1)
            
            ax_map.set_title('Localização e SSH Médio', fontsize=12, fontweight='bold')
            ax_map.legend(loc='upper left')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax_map, shrink=0.8, pad=0.02)
            cbar.set_label('SSH Médio (m)', fontsize=10)
            
            # Add statistics text
            stats_text = f"""Estatísticas SSH Rio de Janeiro:
Média: {ssh_mean:.3f} m
Desvio: {ssh_std:.3f} m
Mínimo: {ssh_min:.3f} m
Máximo: {ssh_max:.3f} m
Amplitude: {ssh_max-ssh_min:.3f} m"""
            
            ax_map.text(0.02, 0.98, stats_text, transform=ax_map.transAxes, 
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                       verticalalignment='top', fontsize=9, fontfamily='monospace')
            
            plt.tight_layout()
            
            # Save
            save_path = self.output_dir / "rio_timeseries_combined.png"
            plt.savefig(save_path, dpi=200, bbox_inches='tight')
            print(f"✅ Série temporal salva: {save_path}")
            
            return fig, save_path
            
        except Exception as e:
            print(f"❌ Erro ao criar série temporal: {e}")
            return None, None
            
    def run_all_visualizations(self):
        """
        Run all visualization tasks
        """
        print("🚀 Iniciando visualizações combinadas SWOT + ERA5...")
        
        results = {}
        
        # 1. Create snapshots
        results['snapshots'] = self.create_all_snapshots()
        
        # 2. Create GIF
        results['gif'] = self.create_animated_gif()
        
        # 3. Create Rio timeseries
        fig, path = self.create_rio_timeseries()
        results['timeseries'] = path
        if fig:
            plt.close(fig)
        
        print("\\n✅ Todas as visualizações concluídas!")
        return results

def main():
    """
    Main execution function
    """
    # File paths
    swot_file = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed/swot_ssh_gridded.nc"
    era5_file = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/era5_waves/era5_waves_akara_20240216_20240220.nc"
    output_dir = "/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/figures/combined"
    
    # Check files exist
    if not Path(swot_file).exists():
        print(f"❌ Arquivo SWOT não encontrado: {swot_file}")
        return
        
    if not Path(era5_file).exists():
        print(f"❌ Arquivo ERA5 não encontrado: {era5_file}")
        return
    
    # Create visualizer and run
    visualizer = CombinedSWOTxERA5Visualizer(swot_file, era5_file, output_dir)
    results = visualizer.run_all_visualizations()
    
    print("\\n📋 Resumo dos resultados:")
    print(f"Snapshots: {len(results.get('snapshots', []))} arquivos")
    print(f"GIF: {'✅' if results.get('gif') else '❌'}")
    print(f"Série temporal: {'✅' if results.get('timeseries') else '❌'}")

if __name__ == "__main__":
    main()