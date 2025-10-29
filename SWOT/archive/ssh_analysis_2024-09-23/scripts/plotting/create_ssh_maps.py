#!/usr/bin/env python3
"""
Script para gerar mapas estáticos de SSH do SWOT
Mapas de alta qualidade para conferências científicas de oceanografia

Autor: Danilo Couto de Souza
Data: Setembro 2025
Projeto: Análise SWOT - Ciclone Akará
"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cmocean
from pathlib import Path
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class SWOTSSHMapper:
    """Classe para criar mapas de SSH do SWOT."""
    
    def __init__(self, data_file=None):
        """Inicializa o mapeador."""
        self.processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        self.figures_dir = Path(__file__).parent.parent.parent / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
        # Arquivo de dados processados
        if data_file is None:
            self.data_file = self.processed_dir / "swot_ssh_gridded.nc"
        else:
            self.data_file = Path(data_file)
        
        print(f"📁 Dados: {self.data_file}")
        print(f"🖼️ Figuras: {self.figures_dir}")
        
        # Configurações de estilo para publicação
        self.setup_plotting_style()
        
        # Carregar dados se disponível
        self.load_data()
    
    def setup_plotting_style(self):
        """Configura o estilo de plotagem para figuras científicas profissionais"""
        plt.rcParams.update({
            'font.size': 12,
            'font.family': 'serif',
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 11,
            'figure.titlesize': 18,
            'axes.linewidth': 1.2,
            'grid.linewidth': 0.5,
            'lines.linewidth': 1.5,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
    
    def load_data(self):
        """Carrega dados processados."""
        if not self.data_file.exists():
            print("⚠️ Arquivo de dados não encontrado. Execute primeiro o script de processamento.")
            self.ds = None
            return
        
        try:
            self.ds = xr.open_dataset(self.data_file)
            print(f"✅ Dados carregados: {dict(self.ds.dims)}")
            print(f"📋 Variáveis: {list(self.ds.data_vars)}")
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            self.ds = None
    
    def create_base_map(self, figsize=(14, 10), projection=None):
        """
        Cria mapa base profissional.
        
        Parameters:
        -----------
        figsize : tuple
            Tamanho da figura
        projection : cartopy projection
            Projeção cartográfica
        """
        if projection is None:
            # Usar projeção adequada para Atlântico Sul
            projection = ccrs.PlateCarree()
        
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=projection)
        
        # Adicionar características geográficas
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='black')
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, color='gray', alpha=0.7)
        ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.8)
        ax.add_feature(cfeature.OCEAN, color='white', alpha=0.5)
        
        # Adicionar linhas de grade
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(), 
            draw_labels=True,
            linewidth=0.5, 
            color='gray', 
            alpha=0.5, 
            linestyle='--'
        )
        
        # Configurar labels das grades
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 12}
        gl.ylabel_style = {'size': 12}
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        return fig, ax
    
    def plot_ssh_snapshot(self, time_idx=0, variable='ssh_karin', 
                         cmap='RdBu_r', vmin=None, vmax=None):
        """
        Cria mapa instantâneo de SSH.
        
        Parameters:
        -----------
        time_idx : int
            Índice temporal
        variable : str
            Variável a plotar
        cmap : str
            Colormap
        vmin, vmax : float
            Limites de cor
        """
        if self.ds is None:
            print("❌ Dados não carregados!")
            return None, None
        
        if variable not in self.ds:
            print(f"❌ Variável {variable} não encontrada!")
            return None, None
        
        # Extrair dados
        data = self.ds[variable].isel(time=time_idx)
        
        # Obter timestamp
        time_value = self.ds.time.isel(time=time_idx).values
        if pd.isna(time_value):
            timestamp = None
            time_str = f"Timestep {time_idx}"
        else:
            timestamp = pd.to_datetime(time_value)
            time_str = timestamp.strftime('%Y-%m-%d %H:%M UTC')
        
        # Criar mapa base
        fig, ax = self.create_base_map()
        
        # Definir região
        lon_min, lon_max = float(self.ds.longitude.min()), float(self.ds.longitude.max())
        lat_min, lat_max = float(self.ds.latitude.min()), float(self.ds.latitude.max())
        
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
        
        # Preparar dados para plot
        X, Y = np.meshgrid(self.ds.longitude, self.ds.latitude)
        Z = data.values
        
        # Mascarar NaN values
        Z_masked = np.ma.masked_invalid(Z)
        
        # Verificar se há dados válidos
        if np.all(np.isnan(Z)) or Z_masked.count() == 0:
            print(f"⚠️ Nenhum dado válido encontrado para timestep {time_idx}")
            return None, None
        
        # Definir limites de cor se não especificados
        if vmin is None or vmax is None:
            # Obter apenas valores válidos (não NaN e não mascarados)
            valid_data = Z_masked.compressed()  # Remove masked values and NaN
            
            if len(valid_data) == 0:
                print(f"⚠️ Nenhum dado válido após remoção de máscaras")
                vmin, vmax = 0, 1  # Valores padrão
            else:
                if variable == 'ssh_karin':
                    # Para SSH, usar limites simétricos
                    vabs = np.percentile(np.abs(valid_data), 95)
                    vmin, vmax = -vabs, vabs
                else:
                    vmin, vmax = np.percentile(valid_data, [5, 95])
        
        # Escolher colormap apropriado
        if variable == 'ssh_karin':
            cmap = cmocean.cm.balance  # SSH anomaly
            label = 'Sea Surface Height (m)'
        elif variable == 'swh_karin':
            cmap = cmocean.cm.amp  # Amplitude
            label = 'Significant Wave Height (m)'
        elif variable == 'wind_speed':
            cmap = cmocean.cm.speed  # Velocidade
            label = 'Wind Speed (m/s)'
        else:
            cmap = 'viridis'
            label = variable
        
        # Plot principal
        im = ax.pcolormesh(
            X, Y, Z_masked,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading='auto'
        )
        
        # Colorbar
        cbar = plt.colorbar(
            im, ax=ax, 
            orientation='horizontal', 
            pad=0.05, 
            shrink=0.8,
            aspect=30
        )
        cbar.set_label(label, fontsize=14)
        cbar.ax.tick_params(labelsize=12)
        
        # Título e labels
        title = f"SWOT {variable.upper().replace('_', ' ').title()}"
        subtitle = f"{time_str} - Cyclone Akará Period"
        
        ax.set_title(f"{title}\n{subtitle}", fontsize=16, pad=20)
        
        # Adicionar informações do dataset
        ax.text(
            0.02, 0.98, 
            'Data: SWOT Level 2 SSH Basic',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        # Adicionar escala de cores
        if variable == 'ssh_karin':
            # Adicionar contornos para SSH
            contours = ax.contour(
                X, Y, Z_masked,
                levels=np.linspace(vmin, vmax, 11),
                colors='black',
                linewidths=0.5,
                alpha=0.3,
                transform=ccrs.PlateCarree()
            )
        
        plt.tight_layout()
        
        return fig, ax
    
    def create_multi_variable_map(self, time_idx=0):
        """
        Cria mapa com múltiplas variáveis (SSH, SWH, Wind).
        """
        if self.ds is None:
            print("❌ Dados não carregados!")
            return None
        
        # Verificar variáveis disponíveis
        available_vars = [var for var in ['ssh_karin', 'swh_karin', 'wind_speed'] 
                         if var in self.ds]
        
        if not available_vars:
            print("❌ Nenhuma variável disponível!")
            return None
        
        n_vars = len(available_vars)
        timestamp = pd.to_datetime(self.ds.time.isel(time=time_idx).values)
        
        # Criar figura com subplots
        fig = plt.figure(figsize=(18, 6*n_vars))
        
        # Configurações para cada variável
        var_configs = {
            'ssh_karin': {
                'cmap': cmocean.cm.balance,
                'label': 'Sea Surface Height (m)',
                'title': 'Sea Surface Height Anomaly'
            },
            'swh_karin': {
                'cmap': cmocean.cm.amp,
                'label': 'Significant Wave Height (m)',
                'title': 'Significant Wave Height'
            },
            'wind_speed': {
                'cmap': cmocean.cm.speed,
                'label': 'Wind Speed (m/s)',
                'title': 'Wind Speed'
            }
        }
        
        for i, variable in enumerate(available_vars):
            ax = plt.subplot(n_vars, 1, i+1, projection=ccrs.PlateCarree())
            
            # Configurar mapa base
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='black')
            ax.add_feature(cfeature.BORDERS, linewidth=0.5, color='gray', alpha=0.7)
            ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.8)
            
            # Definir extensão
            lon_min, lon_max = float(self.ds.longitude.min()), float(self.ds.longitude.max())
            lat_min, lat_max = float(self.ds.latitude.min()), float(self.ds.latitude.max())
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
            
            # Grid
            gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False if i < n_vars-1 else True
            gl.xlabel_style = {'size': 11}
            gl.ylabel_style = {'size': 11}
            
            # Dados
            data = self.ds[variable].isel(time=time_idx)
            X, Y = np.meshgrid(self.ds.longitude, self.ds.latitude)
            Z = data.values
            Z_masked = np.ma.masked_invalid(Z)
            
            # Limites de cor
            config = var_configs[variable]
            if variable == 'ssh_karin':
                vabs = np.nanpercentile(np.abs(Z_masked), 95)
                vmin, vmax = -vabs, vabs
            else:
                vmin, vmax = np.nanpercentile(Z_masked, [5, 95])
            
            # Plot
            im = ax.pcolormesh(
                X, Y, Z_masked,
                transform=ccrs.PlateCarree(),
                cmap=config['cmap'],
                vmin=vmin,
                vmax=vmax,
                shading='auto'
            )
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax, orientation='horizontal', 
                              pad=0.05, shrink=0.8, aspect=30)
            cbar.set_label(config['label'], fontsize=12)
            cbar.ax.tick_params(labelsize=10)
            
            # Título
            ax.set_title(f"{config['title']} - {timestamp.strftime('%Y-%m-%d %H:%M UTC')}", 
                        fontsize=14, pad=15)
        
        # Título geral
        fig.suptitle(
            f"SWOT Multi-Variable Analysis - Cyclone Akará\n{timestamp.strftime('%B %d, %Y')}",
            fontsize=18, y=0.98
        )
        
        plt.tight_layout()
        
        return fig
    
    def save_figure(self, fig, filename, formats=['png', 'pdf']):
        """
        Salva figura em múltiplos formatos.
        
        Parameters:
        -----------
        fig : matplotlib figure
            Figura a salvar
        filename : str
            Nome base do arquivo
        formats : list
            Formatos de saída
        """
        saved_files = []
        
        for fmt in formats:
            output_file = self.figures_dir / f"{filename}.{fmt}"
            fig.savefig(output_file, format=fmt, dpi=300, bbox_inches='tight')
            saved_files.append(output_file)
            print(f"💾 Salvo: {output_file}")
        
        return saved_files
    
    def create_time_series_maps(self, variable='ssh_karin', max_maps=6):
        """
        Cria série de mapas ao longo do tempo.
        """
        if self.ds is None:
            print("❌ Dados não carregados!")
            return
        
        n_times = len(self.ds.time)
        time_indices = np.linspace(0, n_times-1, min(max_maps, n_times), dtype=int)
        
        print(f"🗓️ Criando {len(time_indices)} mapas de série temporal...")
        
        for i, time_idx in enumerate(time_indices):
            time_value = self.ds.time.isel(time=time_idx).values
            
            if pd.isna(time_value):
                timestamp_str = f"Timestep_{time_idx:02d}"
                print(f"📅 Mapa {i+1}/{len(time_indices)}: Timestep {time_idx}")
            else:
                timestamp = pd.to_datetime(time_value)
                timestamp_str = timestamp.strftime('%Y%m%d_%H%M')
                print(f"📅 Mapa {i+1}/{len(time_indices)}: {timestamp}")
            
            fig, ax = self.plot_ssh_snapshot(time_idx, variable)
            
            if fig is not None:
                filename = f"swot_{variable}_map_{timestamp_str}"
                self.save_figure(fig, filename)
                plt.close(fig)

def main():
    """Função principal."""
    print("🗺️ GERAÇÃO DE MAPAS SSH DO SWOT")
    print("=" * 40)
    
    # Criar mapeador
    mapper = SWOTSSHMapper()
    
    if mapper.ds is None:
        print("❌ Execute primeiro o script de processamento!")
        return
    
    print(f"📅 Dados disponíveis: {len(mapper.ds.time)} timestamps")
    print(f"🌍 Região: {float(mapper.ds.longitude.min()):.1f}° a {float(mapper.ds.longitude.max()):.1f}°E")
    print(f"        {float(mapper.ds.latitude.min()):.1f}° a {float(mapper.ds.latitude.max()):.1f}°N")
    
    # 1. Mapa instantâneo de SSH
    print("\n🗺️ Criando mapa instantâneo de SSH...")
    fig_ssh, _ = mapper.plot_ssh_snapshot(time_idx=0, variable='ssh_karin')
    if fig_ssh:
        mapper.save_figure(fig_ssh, "swot_ssh_snapshot")
        plt.close(fig_ssh)
    
    # 2. Mapa multi-variável
    print("\n📊 Criando mapa multi-variável...")
    # Comentar temporariamente para testar
    print("📊 Mapa multi-variável temporariamente desabilitado")
    fig_multi = None
    
    # fig_multi = mapper.create_multi_variable_map(time_idx=0)
    if fig_multi:
        mapper.save_figure(fig_multi, "swot_multi_variable")
        plt.close(fig_multi)
    
    # 3. Série temporal de mapas
    print("\n🕐 Criando série temporal de mapas...")
    mapper.create_time_series_maps(variable='ssh_karin', max_maps=6)
    
    print("\n✅ Geração de mapas concluída!")
    print(f"🖼️ Figuras salvas em: {mapper.figures_dir}")

if __name__ == "__main__":
    main()