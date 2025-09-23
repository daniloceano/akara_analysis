#!/usr/bin/env python3
"""
Script para criar visualizações estilo SWOT com dados combinados SWOT + ERA5.
Snapshots, GIF animado e série temporal com mapa inset para o Rio de Janeiro.

Análise do Ciclone Akará - Fevereiro 2024
Dados combinados: SSH (SWOT) sobreposto em ondas (ERA5)
"""

import os
import sys
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import TwoSlopeNorm
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

class CombinedSWOTxERA5Visualizer:
    """Classe para criar visualizações estilo SWOT com dados combinados."""
    
    def __init__(self, swot_file, era5_file, output_dir):
        """
        Initialize the visualizer with data files
        """
        self.swot_file = swot_file
        self.era5_file = era5_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and process data
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
        
        # Setup Rio coordinates
        self.rio_lat = -22.9068
        self.rio_lon = -43.1729

    def load_data(self):
        """Carregar e sincronizar dados SWOT e ERA5."""
        print("\\n📂 Carregando dados...")
        
        try:
            # Carregar dados SWOT
            swot_files = list(self.swot_dir.glob('*.nc'))
            if not swot_files:
                print("❌ Nenhum arquivo SWOT encontrado!")
                return None, None
            
            swot_data = xr.open_dataset(swot_files[0])
            print(f"✅ SWOT: {len(swot_data.time)} pontos temporais")
            
            # Carregar dados ERA5
            era5_files = list(self.era5_dir.glob('*.nc'))
            if not era5_files:
                print("❌ Nenhum arquivo ERA5 encontrado!")
                return None, None
            
            era5_data = xr.open_dataset(era5_files[0])
            time_var = 'valid_time' if 'valid_time' in era5_data.dims else 'time'
            print(f"✅ ERA5: {len(era5_data[time_var])} pontos temporais")
            
            # Sincronizar dados temporalmente
            # Interpolar ERA5 para os tempos do SWOT
            era5_sync = era5_data.interp({time_var: swot_data['time']}, method='linear')
            print(f"✅ Sincronização temporal: {len(swot_data.time)} pontos comuns")
            
            # Recortar para região de interesse
            swot_region = swot_data.sel(
                latitude=slice(self.region['lat_min'], self.region['lat_max']),
                longitude=slice(self.region['lon_min'], self.region['lon_max'])
            )
            
            era5_region = era5_sync.sel(
                latitude=slice(self.region['lat_min'], self.region['lat_max']),
                longitude=slice(self.region['lon_min'], self.region['lon_max'])
            )
            
            print(f"✅ Dados recortados para região: {self.region}")
            
            return swot_region, era5_region
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return None, None

    def create_snapshot(self, swot_data, era5_data, time_idx, save_path=None):
        """
        Criar snapshot para um momento específico.
        
        Args:
            swot_data: Dados SWOT
            era5_data: Dados ERA5 sincronizados
            time_idx: Índice temporal
            save_path: Caminho para salvar (opcional)
        """
        try:
            # Selecionar dados para o tempo específico
            time_point = swot_data.time[time_idx]
            era5_slice = era5_data.isel(time=time_idx)
            swot_slice = swot_data.isel(time=time_idx)
            
            # Criar figura
            fig, ax = plt.subplots(1, 1, figsize=(12, 10), 
                                 subplot_kw={'projection': ccrs.PlateCarree()})
            
            # 1. Fundo: Altura de ondas ERA5 (cores suaves)
            wave_height = era5_slice['swh']
            im_waves = ax.pcolormesh(
                era5_slice.longitude, era5_slice.latitude, wave_height,
                transform=ccrs.PlateCarree(), cmap='Blues', alpha=0.7,
                vmin=0, vmax=4, zorder=1
            )
            
            # 2. Sobrepor: SSH SWOT (cores contrastantes)
            ssh_data = swot_slice['ssh_karin']
            
            # Máscara para dados válidos do SWOT
            ssh_valid = ~np.isnan(ssh_data)
            
            if ssh_valid.any():
                ssh_norm = TwoSlopeNorm(vmin=-0.5, vcenter=0, vmax=0.5)
                im_ssh = ax.pcolormesh(
                    swot_slice.longitude, swot_slice.latitude, 
                    ssh_data.where(ssh_valid),
                    transform=ccrs.PlateCarree(), cmap='RdBu_r', 
                    norm=ssh_norm, alpha=0.9, zorder=2
                )
                
                # Colorbar para SSH
                cbar_ssh = plt.colorbar(im_ssh, ax=ax, shrink=0.8, pad=0.02)
                cbar_ssh.set_label('SSH SWOT (m)', fontsize=11, fontweight='bold')
            
            # Colorbar para ondas (posição ajustada)
            cbar_waves = plt.colorbar(im_waves, ax=ax, shrink=0.8, pad=0.12)
            cbar_waves.set_label('Altura de Ondas ERA5 (m)', fontsize=11, fontweight='bold')
            
            # Características geográficas
            ax.add_feature(cfeature.COASTLINE, linewidth=1.5)
            ax.add_feature(cfeature.BORDERS, linewidth=1)
            ax.add_feature(cfeature.LAND, alpha=0.3, color='lightgray')
            
            # Marcar ponto do Rio de Janeiro
            ax.plot(self.rio_point['lon'], self.rio_point['lat'], 
                   'ro', markersize=8, markeredgecolor='white', 
                   markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=5)
            ax.text(self.rio_point['lon']+1, self.rio_point['lat']+1, 'Rio de Janeiro',
                   transform=ccrs.PlateCarree(), fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
            # Título com informações
            time_str = pd.to_datetime(time_point.values).strftime('%Y-%m-%d %H:%M UTC')
            ax.set_title(f'Ciclone Akará - {time_str}\\n'
                        f'SSH (SWOT) + Altura de Ondas (ERA5)', 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Grade e labels
            ax.gridlines(draw_labels=True, alpha=0.3)
            ax.set_extent([self.region['lon_min'], self.region['lon_max'],
                          self.region['lat_min'], self.region['lat_max']])
            
            plt.tight_layout()
            
            # Salvar se caminho fornecido
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                return fig
            
        except Exception as e:
            print(f"❌ Erro ao criar snapshot {time_idx}: {e}")
            return None

    def create_all_snapshots(self, swot_data, era5_data):
        """Criar snapshots para todos os momentos temporais."""
        print("\\n📸 Criando snapshots para todos os períodos...")
        
        snapshot_files = []
        n_times = len(swot_data.time)
        
        for i in range(n_times):
            time_point = swot_data.time[i]
            time_str = pd.to_datetime(time_point.values).strftime('%Y%m%d_%H%M')
            
            # Nome do arquivo
            filename = f"snapshot_combined_{time_str}.png"
            filepath = self.combined_dir / filename
            
            # Criar snapshot
            result = self.create_snapshot(swot_data, era5_data, i, filepath)
            
            if result:
                snapshot_files.append(result)
                print(f"✅ Snapshot {i+1}/{n_times}: {filename}")
            else:
                print(f"❌ Falha no snapshot {i+1}/{n_times}")
        
        print(f"\\n📸 {len(snapshot_files)} snapshots criados!")
        return snapshot_files

    def create_animated_gif(self, swot_data, era5_data):
        """Criar GIF animado da sequência temporal."""
        print("\\n🎬 Criando GIF animado...")
        
        try:
            # Criar figura para animação
            fig, ax = plt.subplots(1, 1, figsize=(12, 10), 
                                 subplot_kw={'projection': ccrs.PlateCarree()})
            
            n_times = len(swot_data.time)
            
            def animate(frame):
                ax.clear()
                
                # Selecionar dados para o frame
                era5_slice = era5_data.isel(time=frame)
                swot_slice = swot_data.isel(time=frame)
                time_point = swot_data.time[frame]
                
                # Fundo: Altura de ondas ERA5
                wave_height = era5_slice['swh']
                im_waves = ax.pcolormesh(
                    era5_slice.longitude, era5_slice.latitude, wave_height,
                    transform=ccrs.PlateCarree(), cmap='Blues', alpha=0.7,
                    vmin=0, vmax=4
                )
                
                # Sobrepor: SSH SWOT
                ssh_data = swot_slice['ssh_karin']
                ssh_valid = ~np.isnan(ssh_data)
                
                if ssh_valid.any():
                    ssh_norm = TwoSlopeNorm(vmin=-0.5, vcenter=0, vmax=0.5)
                    im_ssh = ax.pcolormesh(
                        swot_slice.longitude, swot_slice.latitude, 
                        ssh_data.where(ssh_valid),
                        transform=ccrs.PlateCarree(), cmap='RdBu_r', 
                        norm=ssh_norm, alpha=0.9
                    )
                
                # Características geográficas
                ax.add_feature(cfeature.COASTLINE, linewidth=1.5)
                ax.add_feature(cfeature.BORDERS, linewidth=1)
                ax.add_feature(cfeature.LAND, alpha=0.3, color='lightgray')
                
                # Ponto do Rio
                ax.plot(self.rio_point['lon'], self.rio_point['lat'], 
                       'ro', markersize=8, markeredgecolor='white', 
                       markeredgewidth=2, transform=ccrs.PlateCarree())
                
                # Título
                time_str = pd.to_datetime(time_point.values).strftime('%Y-%m-%d %H:%M UTC')
                ax.set_title(f'Ciclone Akará - {time_str}\\n'
                           f'SSH (SWOT) + Altura de Ondas (ERA5)', 
                           fontsize=14, fontweight='bold')
                
                ax.gridlines(draw_labels=True, alpha=0.3)
                ax.set_extent([self.region['lon_min'], self.region['lon_max'],
                              self.region['lat_min'], self.region['lat_max']])
                
                return []
            
            # Criar animação
            anim = animation.FuncAnimation(fig, animate, frames=n_times, 
                                         interval=800, blit=False, repeat=True)
            
            # Salvar GIF
            gif_path = self.combined_dir / "animation_combined_swot_era5.gif"
            anim.save(gif_path, writer='pillow', fps=1.2, dpi=100)
            plt.close()
            
            print(f"✅ GIF animado salvo: {gif_path}")
            return gif_path
            
        except Exception as e:
            print(f"❌ Erro ao criar GIF: {e}")
            return None

    def create_rio_timeseries(self, swot_data, era5_data):
        """Criar série temporal para ponto próximo ao Rio de Janeiro com mapa inset."""
        print("\\n📈 Criando série temporal para Rio de Janeiro...")
        
        try:
            # Extrair séries temporais no ponto do Rio
            rio_ssh = swot_data['ssh_karin'].sel(
                latitude=self.rio_point['lat'], 
                longitude=self.rio_point['lon'], 
                method='nearest'
            )
            
            rio_waves = era5_data['swh'].sel(
                latitude=self.rio_point['lat'], 
                longitude=self.rio_point['lon'], 
                method='nearest'
            )
            
            # Criar figura com subplot para mapa inset
            fig = plt.figure(figsize=(16, 10))
            
            # Layout: série temporal principal + mapa inset
            gs = fig.add_gridspec(2, 3, height_ratios=[3, 1], width_ratios=[3, 3, 1])
            
            # Plot principal: série temporal
            ax_main = fig.add_subplot(gs[0, :])
            
            # Eixo esquerdo: SSH SWOT
            ax_ssh = ax_main
            ssh_valid = ~np.isnan(rio_ssh)
            if ssh_valid.any():
                line1 = ax_ssh.plot(rio_ssh.time[ssh_valid], rio_ssh[ssh_valid], 
                                   'bo-', linewidth=2, markersize=6, label='SSH SWOT', 
                                   markerfacecolor='blue', markeredgecolor='white', markeredgewidth=1)
            ax_ssh.set_ylabel('SSH (m)', color='blue', fontsize=12, fontweight='bold')
            ax_ssh.tick_params(axis='y', labelcolor='blue')
            ax_ssh.grid(True, alpha=0.3)
            
            # Eixo direito: Altura de ondas ERA5
            ax_waves = ax_ssh.twinx()
            line2 = ax_waves.plot(era5_data.time, rio_waves, 
                                 'g-', linewidth=2, label='SWH ERA5', alpha=0.8)
            ax_waves.set_ylabel('Altura de Ondas (m)', color='green', fontsize=12, fontweight='bold')
            ax_waves.tick_params(axis='y', labelcolor='green')
            
            # Título e legendas
            ax_main.set_title(f'Série Temporal - Rio de Janeiro\\n'
                             f'Lat: {self.rio_point["lat"]:.1f}°S, Lon: {abs(self.rio_point["lon"]):.1f}°W\\n'
                             f'Ciclone Akará (16-20 Feb 2024)', 
                             fontsize=14, fontweight='bold', pad=20)
            
            # Legenda combinada
            lines = (line1 if ssh_valid.any() else []) + line2
            labels = [l.get_label() for l in lines]
            ax_main.legend(lines, labels, loc='upper right', fontsize=11)
            
            # Formatação de datas
            ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax_main.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            plt.setp(ax_main.xaxis.get_majorticklabels(), rotation=45)
            
            # Mapa inset
            ax_map = fig.add_subplot(gs[1, :2], projection=ccrs.PlateCarree())
            
            # Dados médios para o mapa
            ssh_mean = swot_data['ssh_karin'].mean(dim='time')
            waves_mean = era5_data['swh'].mean(dim='time')
            
            # Fundo: ondas
            im_waves = ax_map.pcolormesh(
                era5_data.longitude, era5_data.latitude, waves_mean,
                transform=ccrs.PlateCarree(), cmap='Blues', alpha=0.6
            )
            
            # SSH como contornos
            if not np.isnan(ssh_mean).all():
                cs = ax_map.contour(
                    swot_data.longitude, swot_data.latitude, ssh_mean,
                    levels=10, colors='red', linewidths=1, transform=ccrs.PlateCarree()
                )
            
            # Ponto do Rio destacado
            ax_map.plot(self.rio_point['lon'], self.rio_point['lat'], 
                       'ro', markersize=12, markeredgecolor='yellow', 
                       markeredgewidth=3, transform=ccrs.PlateCarree(), zorder=5)
            
            # Características geográficas
            ax_map.add_feature(cfeature.COASTLINE, linewidth=1)
            ax_map.add_feature(cfeature.BORDERS)
            ax_map.add_feature(cfeature.LAND, alpha=0.5, color='lightgray')
            
            ax_map.set_title('Localização do Ponto', fontsize=12, fontweight='bold')
            ax_map.gridlines(draw_labels=True, alpha=0.3)
            ax_map.set_extent([self.region['lon_min'], self.region['lon_max'],
                              self.region['lat_min'], self.region['lat_max']])
            
            plt.tight_layout()
            
            # Salvar
            timeseries_path = self.combined_dir / "timeseries_rio_combined_swot_era5.png"
            plt.savefig(timeseries_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Série temporal do Rio salva: {timeseries_path}")
            return timeseries_path
            
        except Exception as e:
            print(f"❌ Erro na série temporal: {e}")
            return None

def main():
    """Função principal."""
    print("🌊🛰️ VISUALIZAÇÕES ESTILO SWOT COM DADOS COMBINADOS")
    print("=" * 60)
    print("🌀 Ciclone Akará - Análise Integrada")
    print("📅 SSH (SWOT) + Altura de Ondas (ERA5)")
    print("🏙️ Série temporal para Rio de Janeiro")
    
    # Diretório base
    base_dir = Path(__file__).parent.parent.parent
    
    # Criar visualizador
    visualizer = CombinedSWOTxERA5Visualizer(base_dir)
    
    # Carregar dados
    swot_data, era5_data = visualizer.load_data()
    
    if swot_data is None or era5_data is None:
        print("❌ Falha ao carregar dados.")
        sys.exit(1)
    
    print("\\n🎨 Criando visualizações combinadas...")
    
    # 1. Criar todos os snapshots
    snapshot_files = visualizer.create_all_snapshots(swot_data, era5_data)
    
    # 2. Criar GIF animado
    gif_file = visualizer.create_animated_gif(swot_data, era5_data)
    
    # 3. Criar série temporal do Rio de Janeiro
    timeseries_file = visualizer.create_rio_timeseries(swot_data, era5_data)
    
    print("\\n✅ VISUALIZAÇÕES COMBINADAS CONCLUÍDAS!")
    print(f"📸 {len(snapshot_files)} snapshots criados")
    print(f"🎬 GIF animado: {'✅' if gif_file else '❌'}")
    print(f"📈 Série temporal Rio: {'✅' if timeseries_file else '❌'}")
    print(f"📁 Todos os arquivos em: {visualizer.combined_dir}")
    print("🚀 Análise estilo SWOT com dados combinados completa!")

if __name__ == "__main__":
    main()