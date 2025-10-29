#!/usr/bin/env python3
"""
Script para criar visualizações combinadas SWOT + WAVERYS.
Gera mapas e animações mostrando dados observacionais (SWOT) sobrepostos 
com dados de modelo oceânico (WAVERYS).
"""

import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cmocean
from pathlib import Path
from datetime import datetime, timedelta

class CombinedVisualizer:
    """Classe para criar visualizações combinadas SWOT + WAVERYS."""
    
    def __init__(self, swot_file, waverys_file, output_dir):
        """
        Inicializa o visualizador combinado.
        
        Parameters:
        -----------
        swot_file : str or Path
            Caminho para arquivo SWOT processado
        waverys_file : str or Path  
            Caminho para arquivo WAVERYS
        output_dir : str or Path
            Diretório para salvar figuras
        """
        self.swot_file = Path(swot_file)
        self.waverys_file = Path(waverys_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🛰️ Arquivo SWOT: {self.swot_file}")
        print(f"🌊 Arquivo WAVERYS: {self.waverys_file}")
        print(f"📁 Diretório de saída: {self.output_dir}")
        
        # Carregar dados
        self.load_data()
        
    def load_data(self):
        """Carrega e prepara os dados SWOT e WAVERYS."""
        print("📂 Carregando dados...")
        
        # Carregar SWOT
        try:
            self.swot_ds = xr.open_dataset(self.swot_file)
            print(f"✅ SWOT carregado: {dict(self.swot_ds.dims)}")
            
            # Verificar se temos dados válidos
            valid_swot = (~np.isnan(self.swot_ds.ssh_karin)).sum()
            print(f"   📊 Pontos SWOT válidos: {valid_swot.values}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar SWOT: {e}")
            sys.exit(1)
            
        # Carregar WAVERYS
        try:
            self.waverys_ds = xr.open_dataset(self.waverys_file)
            print(f"✅ WAVERYS carregado: {dict(self.waverys_ds.dims)}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar WAVERYS: {e}")
            sys.exit(1)
        
        # Sincronizar dados temporalmente
        self.synchronize_datasets()
        
    def synchronize_datasets(self):
        """Sincroniza os datasets SWOT e WAVERYS temporalmente."""
        print("🕐 Sincronizando datasets temporalmente...")
        
        # Encontrar período comum
        swot_times = pd.to_datetime(self.swot_ds.time.values)
        waverys_times = pd.to_datetime(self.waverys_ds.time.values)
        
        start_time = max(swot_times.min(), waverys_times.min())
        end_time = min(swot_times.max(), waverys_times.max())
        
        print(f"   📅 Período comum: {start_time.date()} a {end_time.date()}")
        
        # Filtrar para período comum
        self.swot_ds = self.swot_ds.sel(time=slice(start_time, end_time))
        self.waverys_ds = self.waverys_ds.sel(time=slice(start_time, end_time))
        
        # Interpolar WAVERYS para tempos do SWOT (se necessário)
        if len(self.swot_ds.time) != len(self.waverys_ds.time):
            print("   🔄 Interpolando WAVERYS para tempos do SWOT...")
            self.waverys_ds = self.waverys_ds.interp(time=self.swot_ds.time)
        
        print(f"   ✅ Sincronização concluída: {len(self.swot_ds.time)} timesteps")
        
    def create_combined_maps(self, n_maps=5):
        """
        Cria mapas combinados SWOT + WAVERYS.
        
        Parameters:
        -----------
        n_maps : int
            Número de mapas a criar
        """
        print(f"🗺️ Criando {n_maps} mapas combinados...")
        
        # Selecionar timesteps uniformemente distribuídos
        time_indices = np.linspace(0, len(self.swot_ds.time)-1, n_maps, dtype=int)
        
        for i, t_idx in enumerate(time_indices):
            time = self.swot_ds.time[t_idx]
            self.create_single_combined_map(time, i+1)
        
        print(f"✅ {n_maps} mapas combinados criados!")
        
    def create_single_combined_map(self, time, map_number):
        """
        Cria um único mapa combinado para um timestep específico.
        
        Parameters:
        -----------
        time : pandas.Timestamp
            Timestamp para o mapa
        map_number : int
            Número do mapa
        """
        # Extrair dados para o timestep
        swot_slice = self.swot_ds.sel(time=time)
        waverys_slice = self.waverys_ds.sel(time=time)
        
        # Criar figura com subplots
        fig = plt.figure(figsize=(20, 12))
        
        # Layout: 2x2 com mapa principal maior
        gs = fig.add_gridspec(2, 3, width_ratios=[2, 1, 1], height_ratios=[1, 1])
        
        # Mapa principal: SSH + SWH
        ax_main = fig.add_subplot(gs[:, 0], projection=ccrs.PlateCarree())
        
        # Mapas auxiliares
        ax_wind = fig.add_subplot(gs[0, 1], projection=ccrs.PlateCarree())
        ax_waves = fig.add_subplot(gs[0, 2], projection=ccrs.PlateCarree())
        ax_period = fig.add_subplot(gs[1, 1], projection=ccrs.PlateCarree())
        ax_comparison = fig.add_subplot(gs[1, 2])  # Sem projeção para gráfico
        
        # === MAPA PRINCIPAL: SSH (SWOT) + SWH (WAVERYS) ===
        self.plot_main_combined_map(ax_main, swot_slice, waverys_slice)
        
        # === MAPA AUXILIAR 1: VENTO ===
        self.plot_wind_map(ax_wind, waverys_slice)
        
        # === MAPA AUXILIAR 2: DIREÇÃO DAS ONDAS ===
        self.plot_wave_direction_map(ax_waves, waverys_slice)
        
        # === MAPA AUXILIAR 3: PERÍODO DAS ONDAS ===
        self.plot_wave_period_map(ax_period, waverys_slice)
        
        # === GRÁFICO DE COMPARAÇÃO ===
        self.plot_comparison_chart(ax_comparison, swot_slice, waverys_slice)
        
        # Título geral
        time_str = pd.to_datetime(time).strftime('%Y-%m-%d %H:%M')
        fig.suptitle(f'Análise Combinada SWOT + WAVERYS - Ciclone Akará\\n{time_str} UTC', 
                     fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # Salvar
        filename = f'combined_map_{map_number:02d}_{pd.to_datetime(time).strftime("%Y%m%d_%H%M")}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   💾 Mapa {map_number} salvo: {filename}")
        
    def plot_main_combined_map(self, ax, swot_slice, waverys_slice):
        """Plota o mapa principal com SSH e SWH."""
        # Adicionar características geográficas
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, alpha=0.7)
        ax.add_feature(cfeature.OCEAN, alpha=0.3, color='lightblue')
        ax.add_feature(cfeature.LAND, alpha=0.8, color='lightgray')
        
        # Plot SWH (WAVERYS) como contornos preenchidos - usar VHM0 (altura significativa)
        waverys_var = 'VHM0' if 'VHM0' in waverys_slice else 'swh'  # Fallback para dados sintéticos antigos
        swh_contour = ax.contourf(waverys_slice.longitude, waverys_slice.latitude,
                                waverys_slice[waverys_var], levels=15, cmap='Blues',
                                alpha=0.7, transform=ccrs.PlateCarree())
        
        # Plot SSH (SWOT) como pontos
        ssh_data = swot_slice.ssh_karin.values
        lon_mesh, lat_mesh = np.meshgrid(swot_slice.longitude.values, swot_slice.latitude.values)
        
        # Converter para 1D para scatter plot
        ssh_flat = ssh_data.flatten()
        lon_flat = lon_mesh.flatten()
        lat_flat = lat_mesh.flatten()
        
        # Máscara de valores válidos
        valid_mask = ~np.isnan(ssh_flat)
        
        if valid_mask.sum() > 0:
            ssh_scatter = ax.scatter(lon_flat[valid_mask], lat_flat[valid_mask],
                                   c=ssh_flat[valid_mask], s=3, cmap=cmocean.cm.balance,
                                   vmin=-0.5, vmax=0.5, transform=ccrs.PlateCarree(),
                                   edgecolors='none', alpha=0.8)
        
        # Colorbars
        # SWH colorbar
        cbar_swh = plt.colorbar(swh_contour, ax=ax, shrink=0.6, pad=0.1, 
                               label='Altura Significativa de Ondas (m)')
        
        # SSH colorbar (se há dados)
        if valid_mask.sum() > 0:
            cbar_ssh = plt.colorbar(ssh_scatter, ax=ax, shrink=0.6, pad=0.15,
                                   label='SSH - SWOT (m)')
        
        # Configurar mapa
        ax.set_title('SSH (SWOT) + Altura Significativa de Ondas (WAVERYS)', 
                    fontsize=12, fontweight='bold')
        ax.gridlines(draw_labels=True, alpha=0.5)
        ax.set_extent([waverys_slice.longitude.min(), waverys_slice.longitude.max(),
                      waverys_slice.latitude.min(), waverys_slice.latitude.max()], 
                     ccrs.PlateCarree())
        
    def plot_wind_map(self, ax, waverys_slice):
        """Plota mapa de altura de ondas wind waves."""
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.LAND, alpha=0.5, color='lightgray')
        
        # Usar VHM0_WW (wind waves) se disponível, senão usar wind_speed como fallback
        if 'VHM0_WW' in waverys_slice:
            var_data = waverys_slice.VHM0_WW
            var_label = 'Wind Waves (m)'
            title = 'Altura Significativa - Wind Waves'
        elif 'wind_speed' in waverys_slice:
            var_data = waverys_slice.wind_speed
            var_label = 'Vento (m/s)'
            title = 'Velocidade do Vento (fallback)'
        else:
            # Se não há dados, usar VHM0 como alternativa
            var_data = waverys_slice.VHM0
            var_label = 'SWH Total (m)'
            title = 'Altura Significativa Total'
        
        # Contornos
        wind_contour = ax.contourf(waverys_slice.longitude, waverys_slice.latitude,
                                 var_data, levels=12, cmap='plasma',
                                 transform=ccrs.PlateCarree())
        
        plt.colorbar(wind_contour, ax=ax, shrink=0.7, label=var_label)
        ax.set_title(title, fontsize=10)
        ax.gridlines(alpha=0.5)
        
    def plot_wave_direction_map(self, ax, waverys_slice):
        """Plota mapa de direção das ondas."""
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.LAND, alpha=0.5, color='lightgray')
        
        # Usar variáveis WAVERYS reais
        swh_var = 'VHM0' if 'VHM0' in waverys_slice else 'swh'
        dir_var = 'VMDR' if 'VMDR' in waverys_slice else 'wave_direction'
        
        # Contornos de altura de ondas como background
        swh_contour = ax.contourf(waverys_slice.longitude, waverys_slice.latitude,
                                waverys_slice[swh_var], levels=10, cmap='Blues', alpha=0.5,
                                transform=ccrs.PlateCarree())
        
        # Vetores de direção das ondas
        skip = 4
        lons_sub = waverys_slice.longitude[::skip]
        lats_sub = waverys_slice.latitude[::skip]
        u_wave = np.cos(np.radians(waverys_slice[dir_var][::skip, ::skip]))
        v_wave = np.sin(np.radians(waverys_slice[dir_var][::skip, ::skip]))
        
        ax.quiver(lons_sub, lats_sub, u_wave, v_wave, scale=20, alpha=0.8,
                 color='red', transform=ccrs.PlateCarree())
        
        ax.set_title('Direção Média das Ondas', fontsize=10)
        ax.gridlines(alpha=0.5)
        
    def plot_wave_period_map(self, ax, waverys_slice):
        """Plota mapa de período das ondas."""
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.LAND, alpha=0.5, color='lightgray')
        
        # Usar VTPK (período de pico) se disponível
        period_var = 'VTPK' if 'VTPK' in waverys_slice else 'wave_period'
        title = 'Período de Pico das Ondas' if 'VTPK' in waverys_slice else 'Período das Ondas'
        
        period_contour = ax.contourf(waverys_slice.longitude, waverys_slice.latitude,
                                   waverys_slice[period_var], levels=12, cmap='cividis',
                                   transform=ccrs.PlateCarree())
        
        plt.colorbar(period_contour, ax=ax, shrink=0.7, label='Período (s)')
        ax.set_title(title, fontsize=10)
        ax.gridlines(alpha=0.5)
        
    def plot_comparison_chart(self, ax, swot_slice, waverys_slice):
        """Plota gráfico de comparação estatística."""
        # Extrair estatísticas
        ssh_data = swot_slice.ssh_karin.values[~np.isnan(swot_slice.ssh_karin.values)]
        
        # Usar variáveis WAVERYS reais se disponíveis
        swh_var = 'VHM0' if 'VHM0' in waverys_slice else 'swh'
        swh_data = waverys_slice[swh_var].values.flatten()
        
        # Terceira variável: período ou vento
        if 'VTPK' in waverys_slice:
            third_data = waverys_slice.VTPK.values.flatten()
            third_label = 'Período (WAVERYS)'
        elif 'wind_speed' in waverys_slice:
            third_data = waverys_slice.wind_speed.values.flatten()
            third_label = 'Vento (WAVERYS)'
        else:
            third_data = waverys_slice.VTM02.values.flatten() if 'VTM02' in waverys_slice else swh_data
            third_label = 'Período Médio (WAVERYS)'
        
        # Estatísticas básicas
        stats = {
            'SSH (SWOT)': [np.mean(ssh_data), np.std(ssh_data), len(ssh_data)] if len(ssh_data) > 0 else [0, 0, 0],
            'SWH (WAVERYS)': [np.mean(swh_data), np.std(swh_data), len(swh_data)],
            third_label: [np.mean(third_data), np.std(third_data), len(third_data)]
        }
        
        # Criar gráfico de barras
        variables = list(stats.keys())
        means = [stats[var][0] for var in variables]
        stds = [stats[var][1] for var in variables]
        
        bars = ax.bar(variables, means, yerr=stds, capsize=5, alpha=0.7,
                     color=['red', 'blue', 'green'])
        
        ax.set_title('Estatísticas Instantâneas', fontsize=10)
        ax.set_ylabel('Valor Médio')
        ax.tick_params(axis='x', rotation=45)
        
        # Adicionar valores nas barras
        for bar, mean in zip(bars, means):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{mean:.2f}', ha='center', va='bottom', fontsize=8)
    
    def create_timeseries_rio(self):
        """Cria série temporal para um ponto fixo próximo ao Rio de Janeiro."""
        print("📈 Criando série temporal para ponto próximo ao Rio de Janeiro...")
        
        # Coordenadas aproximadas do Rio de Janeiro
        rio_lat = -22.9
        rio_lon = -43.2
        
        # Encontrar ponto mais próximo nos dados
        swot_point = self.swot_ds.sel(latitude=rio_lat, longitude=rio_lon, method='nearest')
        waverys_point = self.waverys_ds.sel(latitude=rio_lat, longitude=rio_lon, method='nearest')
        
        # Criar figura
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # SSH do SWOT
        times = pd.to_datetime(swot_point.time.values)
        ssh_values = swot_point.ssh_karin.values
        valid_ssh = ~np.isnan(ssh_values)
        
        axes[0].plot(times[valid_ssh], ssh_values[valid_ssh], 'ro-', label='SWOT SSH', markersize=4)
        axes[0].set_ylabel('SSH (m)')
        axes[0].set_title(f'Série Temporal - Ponto próximo ao Rio de Janeiro\\n'
                         f'Lat: {waverys_point.latitude.values:.2f}°, Lon: {waverys_point.longitude.values:.2f}°')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        
        # SWH do WAVERYS
        swh_var = 'VHM0' if 'VHM0' in waverys_point else 'swh'
        swh_values = waverys_point[swh_var].values
        axes[1].plot(times, swh_values, 'b-', label='WAVERYS SWH', linewidth=2)
        axes[1].set_ylabel('SWH (m)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        # Período ou vento do WAVERYS
        if 'VTPK' in waverys_point:
            third_values = waverys_point.VTPK.values
            third_label = 'WAVERYS Período'
            third_ylabel = 'Período (s)'
        elif 'wind_speed' in waverys_point:
            third_values = waverys_point.wind_speed.values
            third_label = 'WAVERYS Vento'
            third_ylabel = 'Vento (m/s)'
        else:
            third_values = waverys_point.VTM02.values if 'VTM02' in waverys_point else swh_values
            third_label = 'WAVERYS Período Médio'
            third_ylabel = 'Período (s)'
            
        axes[2].plot(times, third_values, 'g-', label=third_label, linewidth=2)
        axes[2].set_ylabel(third_ylabel)
        axes[2].set_xlabel('Data')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()
        
        # Formatar eixo x
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Salvar
        filename = 'timeseries_rio_de_janeiro.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"📊 Série temporal salva: {filename}")

def main():
    """Função principal."""
    print("🎨 VISUALIZAÇÕES COMBINADAS SWOT + WAVERYS")
    print("=" * 60)
    
    # Definir caminhos
    base_dir = Path('/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT')
    swot_file = base_dir / 'data' / 'processed' / 'swot_ssh_gridded.nc'
    waverys_file = base_dir / 'data' / 'waverys' / 'waverys_akara_synthetic.nc'
    output_dir = base_dir / 'figures' / 'combined'
    
    # Verificar se arquivos existem
    if not swot_file.exists():
        print(f"❌ Arquivo SWOT não encontrado: {swot_file}")
        sys.exit(1)
        
    if not waverys_file.exists():
        print(f"❌ Arquivo WAVERYS não encontrado: {waverys_file}")
        sys.exit(1)
    
    # Criar visualizador
    visualizer = CombinedVisualizer(swot_file, waverys_file, output_dir)
    
    # Criar mapas combinados
    visualizer.create_combined_maps(n_maps=5)
    
    # Criar série temporal do Rio de Janeiro
    visualizer.create_timeseries_rio()
    
    print("\\n✅ Todas as visualizações combinadas foram criadas!")
    print(f"📁 Verifique os resultados em: {output_dir}")

if __name__ == "__main__":
    main()