#!/usr/bin/env python3
"""
Script para criar visualizações combinadas SWOT + ERA5.
Compara e integra dados de altura do mar (SWOT) com dados de ondas (ERA5).

Análise do Ciclone Akará - Fevereiro 2024
Região: Atlântico Sul (-50°/-20°, -35°/-15°)
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
import warnings
warnings.filterwarnings('ignore')

class SWOTxERA5Visualizer:
    """Classe para criar visualizações combinadas SWOT + ERA5."""
    
    def __init__(self, base_dir):
        """
        Inicializar visualizador.
        
        Args:
            base_dir: Diretório base do projeto
        """
        self.base_dir = Path(base_dir)
        
        # Diretórios
        self.swot_dir = self.base_dir / 'data' / 'processed'  # Dados SWOT processados
        self.era5_dir = self.base_dir / 'data' / 'era5_waves'
        self.figures_dir = self.base_dir / 'figures'
        
        # Subdiretórios para figuras organizadas
        self.combined_dir = self.figures_dir / 'combined'
        self.comparison_dir = self.figures_dir / 'comparison'
        self.swot_only_dir = self.figures_dir / 'swot_only'
        self.era5_only_dir = self.figures_dir / 'era5_only'
        
        # Criar diretórios se não existem
        for fig_dir in [self.combined_dir, self.comparison_dir, self.swot_only_dir, self.era5_only_dir]:
            fig_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Estrutura de figuras organizada:")
        print(f"   🌊 SWOT apenas: {self.swot_only_dir}")
        print(f"   🌪️ ERA5 apenas: {self.era5_only_dir}")
        print(f"   🔄 Combinadas: {self.combined_dir}")
        print(f"   📊 Comparações: {self.comparison_dir}")

    def load_data(self):
        """Carregar dados SWOT e ERA5."""
        print("\\n📂 Carregando dados...")
        
        # Carregar dados SWOT
        swot_files = list(self.swot_dir.glob('*.nc'))
        if not swot_files:
            print("❌ Nenhum arquivo SWOT encontrado!")
            return None, None
        
        print(f"📊 Encontrados {len(swot_files)} arquivos SWOT")
        
        # Carregar dados ERA5
        era5_files = list(self.era5_dir.glob('*.nc'))
        if not era5_files:
            print("❌ Nenhum arquivo ERA5 encontrado!")
            return None, None
        
        print(f"🌊 Encontrados {len(era5_files)} arquivos ERA5")
        
        try:
            # Abrir dados SWOT (todos os arquivos)
            swot_datasets = []
            for file in sorted(swot_files):
                ds = xr.open_dataset(file)
                swot_datasets.append(ds)
            
            swot_data = xr.concat(swot_datasets, dim='time')
            print(f"✅ SWOT: {len(swot_data.time)} pontos temporais")
            
            # Abrir dados ERA5
            era5_data = xr.open_dataset(era5_files[0])
            time_var = 'valid_time' if 'valid_time' in era5_data.dims else 'time'
            print(f"✅ ERA5: {len(era5_data[time_var])} pontos temporais")
            
            return swot_data, era5_data
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return None, None

    def create_spatial_comparison(self, swot_data, era5_data):
        """Criar comparação espacial SSH vs Altura de Ondas."""
        print("\\n🗺️ Criando comparação espacial...")
        
        try:
            # Detectar variável de tempo no ERA5
            time_var = 'valid_time' if 'valid_time' in era5_data.dims else 'time'
            
            # Calcular médias temporais
            ssh_mean = swot_data['ssh_karin'].mean(dim='time')
            wave_mean = era5_data['swh'].mean(dim=time_var)
            
            # Criar figura
            fig, axes = plt.subplots(1, 3, figsize=(20, 6), 
                                   subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Plot 1: SSH SWOT
            ax1 = axes[0]
            ssh_norm = TwoSlopeNorm(vmin=-0.5, vcenter=0, vmax=0.5)
            im1 = ax1.pcolormesh(swot_data.longitude, swot_data.latitude, ssh_mean, 
                               transform=ccrs.PlateCarree(), cmap='RdBu_r', norm=ssh_norm)
            ax1.add_feature(cfeature.COASTLINE)
            ax1.add_feature(cfeature.BORDERS)
            ax1.set_title('Altura do Mar - SWOT\\n(Média Temporal)', fontsize=12, fontweight='bold')
            plt.colorbar(im1, ax=ax1, label='SSH (m)', shrink=0.8)
            
            # Plot 2: Altura de Ondas ERA5
            ax2 = axes[1]
            im2 = ax2.pcolormesh(era5_data.longitude, era5_data.latitude, wave_mean, 
                               transform=ccrs.PlateCarree(), cmap='viridis')
            ax2.add_feature(cfeature.COASTLINE)
            ax2.add_feature(cfeature.BORDERS)
            ax2.set_title('Altura Significativa de Ondas - ERA5\\n(Média Temporal)', 
                         fontsize=12, fontweight='bold')
            plt.colorbar(im2, ax=ax2, label='SWH (m)', shrink=0.8)
            
            # Plot 3: Mapa combinado (contornos)
            ax3 = axes[2]
            
            # SSH como fundo colorido
            im3 = ax3.pcolormesh(swot_data.longitude, swot_data.latitude, ssh_mean, 
                               transform=ccrs.PlateCarree(), cmap='RdBu_r', norm=ssh_norm, alpha=0.7)
            
            # Ondas como contornos
            cs = ax3.contour(era5_data.longitude, era5_data.latitude, wave_mean, 
                           levels=10, colors='black', linewidths=1.5, transform=ccrs.PlateCarree())
            ax3.clabel(cs, inline=True, fontsize=8, fmt='%.1f m')
            
            ax3.add_feature(cfeature.COASTLINE)
            ax3.add_feature(cfeature.BORDERS)
            ax3.set_title('Combinado: SSH (cor) + Ondas (contornos)\\nCiclone Akará', 
                         fontsize=12, fontweight='bold')
            
            # Colorbar para SSH
            cbar3 = plt.colorbar(im3, ax=ax3, label='SSH (m)', shrink=0.8)
            
            # Adicionar título geral
            fig.suptitle('Análise Integrada SWOT + ERA5 - Ciclone Akará (16-20 Feb 2024)', 
                        fontsize=16, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            
            # Salvar
            output_file = self.combined_dir / 'spatial_comparison_swot_era5.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Comparação espacial salva: {output_file}")
            
        except Exception as e:
            print(f"❌ Erro na comparação espacial: {e}")

    def create_temporal_analysis(self, swot_data, era5_data):
        """Criar análise temporal coordenada."""
        print("\\n📈 Criando análise temporal...")
        
        try:
            # Detectar variável de tempo no ERA5
            time_var = 'valid_time' if 'valid_time' in era5_data.dims else 'time'
            
            # Ponto central da região
            center_lat = -25.0
            center_lon = -35.0
            
            # Séries temporais no ponto central
            ssh_series = swot_data['ssh_karin'].sel(latitude=center_lat, longitude=center_lon, method='nearest')
            wave_series = era5_data['swh'].sel(latitude=center_lat, longitude=center_lon, method='nearest')
            
            # Criar figura com subplots
            fig, axes = plt.subplots(3, 1, figsize=(15, 12))
            
            # Plot 1: SSH SWOT
            ax1 = axes[0]
            ssh_series.plot(ax=ax1, color='blue', linewidth=2, label='SSH SWOT')
            ax1.set_title(f'Altura do Mar (SSH) - SWOT\\nPonto: {center_lat:.1f}°S, {abs(center_lon):.1f}°W', 
                         fontweight='bold')
            ax1.set_ylabel('SSH (m)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Plot 2: Altura de Ondas ERA5
            ax2 = axes[1]
            wave_series.plot(ax=ax2, color='green', linewidth=2, label='SWH ERA5')
            ax2.set_title('Altura Significativa de Ondas - ERA5', fontweight='bold')
            ax2.set_ylabel('SWH (m)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Plot 3: Comparação combinada (eixos duplos)
            ax3 = axes[2]
            
            # SSH no eixo esquerdo
            ax3_left = ax3
            line1 = ax3_left.plot(ssh_series.time, ssh_series, 'b-', linewidth=2, label='SSH (SWOT)')
            ax3_left.set_ylabel('SSH (m)', color='blue')
            ax3_left.tick_params(axis='y', labelcolor='blue')
            
            # Ondas no eixo direito
            ax3_right = ax3_left.twinx()
            line2 = ax3_right.plot(era5_data[time_var], wave_series, 'g-', linewidth=2, label='SWH (ERA5)')
            ax3_right.set_ylabel('SWH (m)', color='green')
            ax3_right.tick_params(axis='y', labelcolor='green')
            
            # Título e legenda
            ax3.set_title('Comparação Temporal: SSH vs Altura de Ondas', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # Legenda combinada
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax3.legend(lines, labels, loc='upper right')
            
            # Formatação de datas
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Salvar
            output_file = self.comparison_dir / 'temporal_analysis_swot_era5.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Análise temporal salva: {output_file}")
            
        except Exception as e:
            print(f"❌ Erro na análise temporal: {e}")

    def create_correlation_analysis(self, swot_data, era5_data):
        """Criar análise de correlação entre SSH e ondas."""
        print("\\n🔗 Criando análise de correlação...")
        
        try:
            # Detectar variável de tempo no ERA5
            time_var = 'valid_time' if 'valid_time' in era5_data.dims else 'time'
            
            # Interpolar dados para mesma grade temporal
            # Usar tempo do SWOT como referência (menos pontos mas compatível)
            era5_interp = era5_data.interp({time_var: swot_data['time']}, method='linear')
            
            # Calcular correlação ponto a ponto
            ssh_vals = swot_data['ssh_karin'].values
            swh_vals = era5_interp['swh'].values
            
            # Correlação espacial
            correlation_map = np.full_like(ssh_vals[0], np.nan)
            
            for i in range(ssh_vals.shape[1]):  # latitude
                for j in range(ssh_vals.shape[2]):  # longitude
                    ssh_ts = ssh_vals[:, i, j]
                    swh_ts = swh_vals[:, i, j]
                    
                    # Remover NaNs
                    mask = ~(np.isnan(ssh_ts) | np.isnan(swh_ts))
                    if np.sum(mask) > 10:  # Pelo menos 10 pontos válidos
                        correlation_map[i, j] = np.corrcoef(ssh_ts[mask], swh_ts[mask])[0, 1]
            
            # Criar figura
            fig, axes = plt.subplots(1, 2, figsize=(16, 6),
                                   subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Plot 1: Mapa de correlação
            ax1 = axes[0]
            im1 = ax1.pcolormesh(swot_data.longitude, swot_data.latitude, correlation_map,
                               transform=ccrs.PlateCarree(), cmap='RdBu_r', 
                               vmin=-1, vmax=1)
            ax1.add_feature(cfeature.COASTLINE)
            ax1.add_feature(cfeature.BORDERS)
            ax1.set_title('Correlação SSH vs SWH\\n(Ciclone Akará)', fontweight='bold')
            plt.colorbar(im1, ax=ax1, label='Correlação', shrink=0.8)
            
            # Plot 2: Scatter plot
            ax2 = axes[1]
            
            # Flatten arrays e remover NaNs
            ssh_flat = ssh_vals.flatten()
            swh_flat = swh_vals.flatten()
            mask = ~(np.isnan(ssh_flat) | np.isnan(swh_flat))
            
            ssh_clean = ssh_flat[mask]
            swh_clean = swh_flat[mask]
            
            # Scatter plot com densidade
            ax2.hexbin(ssh_clean, swh_clean, gridsize=50, cmap='Blues', alpha=0.8)
            
            # Linha de tendência
            z = np.polyfit(ssh_clean, swh_clean, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(ssh_clean.min(), ssh_clean.max(), 100)
            ax2.plot(x_trend, p(x_trend), 'r--', linewidth=2, label=f'Tendência: y={z[0]:.3f}x+{z[1]:.3f}')
            
            # Correlação geral
            corr_total = np.corrcoef(ssh_clean, swh_clean)[0, 1]
            ax2.set_xlabel('SSH (m)')
            ax2.set_ylabel('SWH (m)')
            ax2.set_title(f'SSH vs SWH\\nCorrelação: {corr_total:.3f}', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            
            # Salvar
            output_file = self.comparison_dir / 'correlation_analysis_swot_era5.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Análise de correlação salva: {output_file}")
            print(f"📊 Correlação geral SSH vs SWH: {corr_total:.3f}")
            
        except Exception as e:
            print(f"❌ Erro na análise de correlação: {e}")

def main():
    """Função principal."""
    print("🌊🛰️ VISUALIZAÇÕES COMBINADAS SWOT + ERA5")
    print("=" * 60)
    print("🌀 Análise Integrada do Ciclone Akará")
    print("📅 Período: 16-20 Fevereiro 2024")
    print("🌍 Região: Atlântico Sul")
    
    # Diretório base
    base_dir = Path(__file__).parent.parent.parent
    
    # Criar visualizador
    visualizer = SWOTxERA5Visualizer(base_dir)
    
    # Carregar dados
    swot_data, era5_data = visualizer.load_data()
    
    if swot_data is None or era5_data is None:
        print("❌ Falha ao carregar dados. Verifique se os arquivos existem.")
        sys.exit(1)
    
    print("\\n🎨 Criando visualizações...")
    
    # Criar visualizações
    visualizer.create_spatial_comparison(swot_data, era5_data)
    visualizer.create_temporal_analysis(swot_data, era5_data)
    visualizer.create_correlation_analysis(swot_data, era5_data)
    
    print("\\n✅ VISUALIZAÇÕES COMBINADAS CONCLUÍDAS!")
    print("📊 Figuras organizadas em:")
    print(f"   🔄 Combinadas: {visualizer.combined_dir}")
    print(f"   📈 Comparações: {visualizer.comparison_dir}")
    print("🚀 Análise integrada SWOT + ERA5 completa!")

if __name__ == "__main__":
    main()