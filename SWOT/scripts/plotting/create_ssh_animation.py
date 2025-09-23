#!/usr/bin/env python3
"""
Script para criar animação profissional dos dados SSH do SWOT
Animação de alta qualidade para apresentações em congressos

Autor: Danilo Couto de Souza
Data: Setembro 2025
Projeto: Análise SWOT - Ciclone Akará - Waves Workshop
"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cmocean
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class SWOTSSHAnimator:
    """Classe para criar animações dos dados SSH do SWOT."""
    
    def __init__(self, data_file=None):
        """Inicializa o animador."""
        self.processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        self.figures_dir = Path(__file__).parent.parent.parent / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
        # Arquivo de dados processados
        if data_file is None:
            self.data_file = self.processed_dir / "swot_ssh_gridded.nc"
        else:
            self.data_file = Path(data_file)
        
        print(f"📁 Dados: {self.data_file}")
        print(f"🎬 Animações: {self.figures_dir}")
        
        # Configurações de estilo para apresentação
        self.setup_plotting_style()
        
        # Carregar dados
        self.load_data()
    
    def setup_plotting_style(self):
        """Configura estilo escuro profissional para apresentações"""
        plt.style.use('dark_background')
        plt.rcParams.update({
            'font.size': 14,
            'font.family': 'sans-serif',
            'axes.labelsize': 16,
            'axes.titlesize': 18,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12,
            'figure.titlesize': 20,
            'axes.linewidth': 1.5,
            'grid.linewidth': 0.8,
            'lines.linewidth': 2,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.facecolor': 'black',
            'axes.facecolor': 'black',
            'figure.facecolor': 'black'
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
            
            # Pré-calcular limites globais para animação consistente
            self.calculate_global_limits()
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            self.ds = None
    
    def calculate_global_limits(self):
        """Calcula limites globais para todas as variáveis."""
        self.global_limits = {}
        
        for var in ['ssh_karin', 'swh_karin', 'wind_speed']:
            if var in self.ds:
                data = self.ds[var].values
                valid_data = data[~np.isnan(data)]
                
                if len(valid_data) > 0:
                    if var == 'ssh_karin':
                        # SSH: limites simétricos
                        vabs = np.percentile(np.abs(valid_data), 95)
                        self.global_limits[var] = {'vmin': -vabs, 'vmax': vabs}
                    else:
                        # Outras variáveis: percentis
                        vmin, vmax = np.percentile(valid_data, [5, 95])
                        self.global_limits[var] = {'vmin': vmin, 'vmax': vmax}
                    
                    print(f"📊 {var}: [{self.global_limits[var]['vmin']:.3f}, {self.global_limits[var]['vmax']:.3f}]")
    
    def create_animation_base(self, figsize=(16, 10)):
        """
        Cria base para animação.
        
        Parameters:
        -----------
        figsize : tuple
            Tamanho da figura
        """
        # Projeção adequada para Atlântico Sul
        projection = ccrs.PlateCarree()
        
        fig = plt.figure(figsize=figsize, facecolor='black')
        ax = plt.axes(projection=projection)
        
        # Características geográficas com estilo escuro
        ax.add_feature(cfeature.COASTLINE, linewidth=1.2, color='gold', alpha=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, color='white', alpha=0.5)
        ax.add_feature(cfeature.LAND, color='#2F2F2F', alpha=0.9)
        ax.add_feature(cfeature.OCEAN, color='#1a1a1a', alpha=0.9)
        
        # Grid mais visível
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(), 
            draw_labels=True,
            linewidth=1.0, 
            color='white', 
            alpha=0.4, 
            linestyle='-'
        )
        
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 14, 'color': 'white', 'weight': 'bold'}
        gl.ylabel_style = {'size': 14, 'color': 'white', 'weight': 'bold'}
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        
        # Definir extensão
        if self.ds is not None:
            lon_min, lon_max = float(self.ds.longitude.min()), float(self.ds.longitude.max())
            lat_min, lat_max = float(self.ds.latitude.min()), float(self.ds.latitude.max())
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
        
        return fig, ax
    
    def create_ssh_animation(self, variable='ssh_karin', fps=2, duration_seconds=10):
        """
        Cria animação de SSH com estilo profissional.
        
        Parameters:
        -----------
        variable : str
            Variável a animar
        fps : int
            Frames por segundo
        duration_seconds : int
            Duração total em segundos
        """
        if self.ds is None:
            print("❌ Dados não carregados!")
            return None
        
        if variable not in self.ds:
            print(f"❌ Variável {variable} não encontrada!")
            return None
        
        print(f"🎬 Criando animação de {variable}...")
        
        # Calcular número de frames
        total_frames = fps * duration_seconds
        n_times = len(self.ds.time)
        time_indices = np.linspace(0, n_times-1, min(total_frames, n_times), dtype=int)
        
        print(f"🎞️ {len(time_indices)} frames, {fps} FPS")
        
        # Criar figura base
        fig, ax = self.create_animation_base()
        
        # Preparar dados
        X, Y = np.meshgrid(self.ds.longitude, self.ds.latitude)
        
        # Configurações da variável
        if variable == 'ssh_karin':
            cmap = cmocean.cm.balance
            title_var = 'Sea Surface Height Anomaly'
            label = 'SSH (m)'
        elif variable == 'swh_karin':
            cmap = cmocean.cm.amp
            title_var = 'Significant Wave Height'
            label = 'SWH (m)'
        elif variable == 'wind_speed':
            cmap = cmocean.cm.speed
            title_var = 'Wind Speed'
            label = 'Wind Speed (m/s)'
        else:
            cmap = 'plasma'
            title_var = variable.replace('_', ' ').title()
            label = variable
        
        # Limites de cor
        if variable in self.global_limits:
            vmin = self.global_limits[variable]['vmin']
            vmax = self.global_limits[variable]['vmax']
        else:
            vmin, vmax = None, None
        
        # Plot inicial
        data_init = self.ds[variable].isel(time=time_indices[0])
        Z_init = np.ma.masked_invalid(data_init.values)
        
        im = ax.pcolormesh(
            X, Y, Z_init,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading='auto'
        )
        
        # Colorbar customizada
        cbar = plt.colorbar(
            im, ax=ax, 
            orientation='horizontal', 
            pad=0.05, 
            shrink=0.7,
            aspect=25
        )
        cbar.set_label(label, fontsize=16, color='white', weight='bold')
        cbar.ax.tick_params(labelsize=14, colors='white')
        cbar.outline.set_edgecolor('white')
        
        # Título dinâmico
        timestamp_init = pd.to_datetime(self.ds.time.isel(time=time_indices[0]).values)
        title = ax.set_title('', fontsize=20, color='white', weight='bold', pad=20)
        
        # Texto de informação
        info_text = ax.text(
            0.02, 0.98,
            '',
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment='top',
            color='white',
            weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='gold')
        )
        
        # Adicionar logo/marca d'água
        ax.text(
            0.98, 0.02,
            'SWOT Analysis\nCyclone Akará\nWaves Workshop 2025',
            transform=ax.transAxes,
            fontsize=10,
            horizontalalignment='right',
            verticalalignment='bottom',
            color='gold',
            weight='bold',
            alpha=0.8
        )
        
        def animate(frame):
            """Função de animação."""
            time_idx = time_indices[frame]
            timestamp = pd.to_datetime(self.ds.time.isel(time=time_idx).values)
            
            # Atualizar dados
            data = self.ds[variable].isel(time=time_idx)
            Z = np.ma.masked_invalid(data.values)
            
            # Atualizar plot
            im.set_array(Z.ravel())
            
            # Obter timestamp
            time_val = self.ds.time.isel(time=time_idx).values
            
            data = self.ds[variable].isel(time=time_idx)
            Z = np.ma.masked_invalid(data.values)
            
            # Atualizar plot
            im.set_array(Z.ravel())
            
            # Atualizar título
            if pd.isna(time_val):
                time_str = f"Timestep {time_idx}"
                day_text = f"Frame {time_idx}"
            else:
                timestamp = pd.to_datetime(time_val)
                time_str = timestamp.strftime('%B %d, %Y - %H:%M UTC')
                try:
                    day_from_start = (timestamp - pd.to_datetime(self.ds.time.min().values)).days
                    day_text = f"Day {day_from_start} from start"
                except:
                    day_text = f"Frame {time_idx}"
            
            title.set_text(
                f"SWOT {title_var}\n"
                f"{time_str}\n"
                f"Cyclone Akará Period"
            )
            
            # Atualizar info
            info_text.set_text(day_text)
            
            # Atualizar info
            day_from_start = (timestamp - pd.to_datetime(self.ds.time.min().values)).days
            info_text.set_text(
                f"Frame: {frame+1}/{len(time_indices)}\n"
                f"Day: +{day_from_start}\n"
                f"Data: SWOT L2 SSH"
            )
            
            return [im, title, info_text]
        
        # Criar animação
        anim = animation.FuncAnimation(
            fig, animate, 
            frames=len(time_indices),
            interval=1000//fps,  # Intervalo em ms
            blit=True,
            repeat=True
        )
        
        return anim, fig
    
    def create_multi_variable_animation(self, fps=2, duration_seconds=8):
        """
        Cria animação com múltiplas variáveis lado a lado.
        """
        if self.ds is None:
            print("❌ Dados não carregados!")
            return None
        
        # Verificar variáveis disponíveis
        available_vars = [var for var in ['ssh_karin', 'swh_karin', 'wind_speed'] 
                         if var in self.ds]
        
        if len(available_vars) < 2:
            print("❌ Pelo menos 2 variáveis necessárias!")
            return None
        
        print(f"🎬 Criando animação multi-variável: {available_vars}")
        
        # Calcular frames
        total_frames = fps * duration_seconds
        n_times = len(self.ds.time)
        time_indices = np.linspace(0, n_times-1, min(total_frames, n_times), dtype=int)
        
        # Criar figura grande
        n_vars = len(available_vars)
        fig = plt.figure(figsize=(8*n_vars, 10), facecolor='black')
        
        axes = []
        ims = []
        titles = []
        
        # Configurações para cada variável
        var_configs = {
            'ssh_karin': {
                'cmap': cmocean.cm.balance,
                'label': 'SSH (m)',
                'title': 'Sea Surface Height'
            },
            'swh_karin': {
                'cmap': cmocean.cm.amp,
                'label': 'SWH (m)',
                'title': 'Wave Height'
            },
            'wind_speed': {
                'cmap': cmocean.cm.speed,
                'label': 'Wind (m/s)',
                'title': 'Wind Speed'
            }
        }
        
        # Criar subplots
        for i, variable in enumerate(available_vars):
            ax = plt.subplot(1, n_vars, i+1, projection=ccrs.PlateCarree())
            axes.append(ax)
            
            # Configurar mapa
            ax.add_feature(cfeature.COASTLINE, linewidth=1.0, color='gold')
            ax.add_feature(cfeature.LAND, color='#2F2F2F', alpha=0.9)
            ax.add_feature(cfeature.OCEAN, color='#1a1a1a', alpha=0.9)
            
            # Extensão
            lon_min, lon_max = float(self.ds.longitude.min()), float(self.ds.longitude.max())
            lat_min, lat_max = float(self.ds.latitude.min()), float(self.ds.latitude.max())
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
            
            # Grid
            gl = ax.gridlines(draw_labels=True, color='white', alpha=0.3)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'size': 12, 'color': 'white'}
            gl.ylabel_style = {'size': 12, 'color': 'white'}
            
            # Dados iniciais
            X, Y = np.meshgrid(self.ds.longitude, self.ds.latitude)
            data_init = self.ds[variable].isel(time=time_indices[0])
            Z_init = np.ma.masked_invalid(data_init.values)
            
            # Limites
            if variable in self.global_limits:
                vmin = self.global_limits[variable]['vmin']
                vmax = self.global_limits[variable]['vmax']
            else:
                vmin, vmax = None, None
            
            config = var_configs[variable]
            
            # Plot
            im = ax.pcolormesh(
                X, Y, Z_init,
                transform=ccrs.PlateCarree(),
                cmap=config['cmap'],
                vmin=vmin,
                vmax=vmax,
                shading='auto'
            )
            ims.append(im)
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax, orientation='horizontal', 
                              pad=0.05, shrink=0.8, aspect=20)
            cbar.set_label(config['label'], fontsize=12, color='white')
            cbar.ax.tick_params(labelsize=10, colors='white')
            cbar.outline.set_edgecolor('white')
            
            # Título
            title = ax.set_title('', fontsize=16, color='white', weight='bold')
            titles.append(title)
        
        # Título geral
        main_title = fig.suptitle('', fontsize=22, color='white', weight='bold', y=0.95)
        
        def animate(frame):
            """Função de animação."""
            time_idx = time_indices[frame]
            timestamp = pd.to_datetime(self.ds.time.isel(time=time_idx).values)
            
            # Atualizar título principal
            main_title.set_text(
                f"SWOT Multi-Variable Analysis - {timestamp.strftime('%B %d, %Y %H:%M UTC')}\n"
                f"Cyclone Akará - Waves Workshop 2025"
            )
            
            # Atualizar cada subplot
            updated_artists = [main_title]
            
            for i, variable in enumerate(available_vars):
                # Atualizar dados
                data = self.ds[variable].isel(time=time_idx)
                Z = np.ma.masked_invalid(data.values)
                ims[i].set_array(Z.ravel())
                
                # Atualizar título
                config = var_configs[variable]
                titles[i].set_text(config['title'])
                
                updated_artists.extend([ims[i], titles[i]])
            
            return updated_artists
        
        # Criar animação
        anim = animation.FuncAnimation(
            fig, animate,
            frames=len(time_indices),
            interval=1000//fps,
            blit=True,
            repeat=True
        )
        
        plt.tight_layout()
        
        return anim, fig
    
    def save_animation(self, anim, filename, format='mp4', fps=2):
        """
        Salva animação em arquivo.
        
        Parameters:
        -----------
        anim : matplotlib animation
            Animação a salvar
        filename : str
            Nome do arquivo
        format : str
            Formato de saída ('mp4', 'gif')
        fps : int
            Frames por segundo
        """
        output_file = self.figures_dir / f"{filename}.{format}"
        
        print(f"💾 Salvando animação: {output_file}")
        
        try:
            if format == 'mp4':
                # Salvar como MP4 (melhor qualidade)
                writer = animation.FFMpegWriter(
                    fps=fps,
                    metadata=dict(artist='SWOT Analysis - Cyclone Akará'),
                    bitrate=5000,  # Alta qualidade
                    extra_args=['-vcodec', 'libx264']
                )
                anim.save(output_file, writer=writer)
                
            elif format == 'gif':
                # Salvar como GIF (menor arquivo)
                writer = animation.PillowWriter(fps=fps)
                anim.save(output_file, writer=writer)
            
            print(f"✅ Animação salva: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Erro ao salvar animação: {e}")
            print("💡 Dica: Instale ffmpeg para MP4 ou Pillow para GIF")
            return None

def main():
    """Função principal."""
    print("🎬 CRIAÇÃO DE ANIMAÇÕES SSH DO SWOT")
    print("=" * 45)
    
    # Criar animador
    animator = SWOTSSHAnimator()
    
    if animator.ds is None:
        print("❌ Execute primeiro o script de processamento!")
        return
    
    print(f"📅 Dados disponíveis: {len(animator.ds.time)} timestamps")
    
    # 1. Animação SSH
    print("\n🌊 Criando animação de SSH...")
    anim_ssh, fig_ssh = animator.create_ssh_animation(
        variable='ssh_karin', 
        fps=2, 
        duration_seconds=10
    )
    
    if anim_ssh:
        animator.save_animation(anim_ssh, "swot_ssh_animation", format='mp4', fps=2)
        animator.save_animation(anim_ssh, "swot_ssh_animation", format='gif', fps=1)
        plt.close(fig_ssh)
    
    # 2. Animação multi-variável (comentado - apenas SSH disponível)
    print("\n📊 Criando animação multi-variável...")
    print("⚠️ Animação multi-variável desabilitada - apenas SSH disponível")
    
    # anim_multi, fig_multi = animator.create_multi_variable_animation(
    #     fps=2, 
    #     duration_seconds=8
    # )
    # 
    # if anim_multi:
    #     animator.save_animation(anim_multi, "swot_multi_animation", format='mp4', fps=2)
    #     plt.close(fig_multi)
    
    print("\n✅ Animações criadas com sucesso!")
    print(f"🎬 Arquivos salvos em: {animator.figures_dir}")
    print("\n🎯 Perfeito para apresentações no Waves Workshop!")

if __name__ == "__main__":
    main()