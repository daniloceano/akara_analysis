"""
Script para plotar trajetórias dos satélites durante o evento Akará
Gera figura mostrando todas as passagens com datas e produtos
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

# Cores para cada satélite (paleta vibrante)
SATELLITE_COLORS = {
    'CFOSAT': '#00FFFF',        # Cyan
    'CryoSat-2': '#FF1493',     # Deep Pink
    'HaiYang-2B': '#FFD700',    # Gold
    'HaiYang-2C': '#FF8C00',    # Dark Orange
    'Jason-3': '#00FF00',       # Lime
    'Saral/AltiKa': '#FF0000',  # Red
    'Sentinel-3A': '#FFFF00',   # Yellow
    'Sentinel-3B': '#00CED1',   # Dark Turquoise
    'Sentinel-6A': '#9370DB',   # Medium Purple
    'SWOT_nadir': '#FF69B4',    # Hot Pink
}


def load_satellite_data(data_dir='data'):
    """
    Carrega dados de todos os satélites disponíveis
    
    Returns
    -------
    dict
        Dicionário com dados de cada satélite {nome: dataframe}
    """
    data_path = PROJECT_ROOT / data_dir
    satellite_data = {}
    
    logger.info("🔍 Procurando dados de satélites...")
    
    for satellite in DATASETS.keys():
        satellite_dir = data_path / satellite.replace('/', '_')
        
        if not satellite_dir.exists():
            logger.warning(f"⚠️  Diretório não encontrado: {satellite}")
            continue
        
        # Procurar arquivo CSV (formato do copernicusmarine)
        csv_files = list(satellite_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"⚠️  Nenhum arquivo CSV encontrado para {satellite}")
            continue
        
        # Carregar primeiro arquivo encontrado
        csv_file = csv_files[0]
        try:
            df = pd.read_csv(csv_file)
            
            # Verificar se há dados
            if len(df) > 0:
                # Converter time para datetime
                df['time'] = pd.to_datetime(df['time'])
                satellite_data[satellite] = df
                logger.info(f"✅ {satellite}: {len(df)} pontos carregados")
            else:
                logger.warning(f"⚠️  {satellite}: sem dados na região")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {satellite}: {str(e)}")
    
    return satellite_data


def plot_satellite_tracks(satellite_data, output_file='figures/satellite_tracks_akara.png'):
    """
    Plota trajetórias de todos os satélites em um mapa
    
    Parameters
    ----------
    satellite_data : dict
        Dados de cada satélite (dataframes)
    output_file : str
        Caminho para salvar a figura
    """
    logger.info("🎨 Criando figura...")
    
    # Criar figura com projeção cartográfica
    fig = plt.figure(figsize=(14, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Definir limites do mapa (região de interesse expandida para contexto)
    margin = 2.0
    ax.set_extent([
        BBOX['west'] - margin,
        BBOX['east'] + margin,
        BBOX['south'] - margin,
        BBOX['north'] + margin
    ], crs=ccrs.PlateCarree())
    
    # Adicionar features geográficos
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.5)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', alpha=0.7)
    
    # Grid
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Plotar caixa da região de interesse
    box_lons = [BBOX['west'], BBOX['east'], BBOX['east'], BBOX['west'], BBOX['west']]
    box_lats = [BBOX['south'], BBOX['south'], BBOX['north'], BBOX['north'], BBOX['south']]
    ax.plot(box_lons, box_lats, 'k--', linewidth=2, transform=ccrs.PlateCarree(), 
            label='Região de Interesse', alpha=0.8)
    
    # Plotar trajetórias de cada satélite
    legend_handles = []
    
    for satellite, df in satellite_data.items():
        color = SATELLITE_COLORS.get(satellite, '#FFFFFF')
        
        try:
            # Extrair coordenadas (filtrando por variável VAVH para evitar duplicatas)
            df_vavh = df[df['variable'] == 'VAVH'].copy()
            
            if len(df_vavh) == 0:
                logger.warning(f"⚠️  {satellite}: sem dados de VAVH")
                continue
            
            lons = df_vavh['longitude'].values
            lats = df_vavh['latitude'].values
            times = df_vavh['time'].values
            
            # Remover NaNs
            valid_mask = ~(np.isnan(lons) | np.isnan(lats))
            lons = lons[valid_mask]
            lats = lats[valid_mask]
            times = times[valid_mask]
            
            if len(lons) == 0:
                continue
            
            # Plotar trajetória
            line = ax.scatter(lons, lats, c=color, s=30, alpha=0.7, 
                            transform=ccrs.PlateCarree(), 
                            edgecolors='black', linewidth=0.5,
                            label=satellite, zorder=5)
            
            # Adicionar labels com datas em pontos estratégicos
            # Selecionar alguns pontos ao longo da trajetória
            n_labels = min(3, len(times))
            if n_labels > 0:
                indices = np.linspace(0, len(times)-1, n_labels, dtype=int)
                
                for idx in indices:
                    date_obj = pd.to_datetime(times[idx])
                    label_text = f"{date_obj.day}.{date_obj.month}"
                    
                    # Adicionar texto com fundo branco semi-transparente
                    ax.text(lons[idx], lats[idx], label_text, 
                           fontsize=7, ha='center', va='bottom',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                   alpha=0.7, edgecolor=color, linewidth=1),
                           transform=ccrs.PlateCarree(), zorder=6)
            
            logger.info(f"✅ Plotado {satellite}: {len(lons)} pontos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao plotar {satellite}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Título
    plt.title(f'🛰️ Passagens de Satélites - Ciclone Akará 🌀\n'
              f'{START_DATE} a {END_DATE}', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Legenda
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), 
             fontsize=10, framealpha=0.9, 
             title='Satélites', title_fontsize=11)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Criar diretório de saída se não existir
    output_path = PROJECT_ROOT / output_file
    output_path.parent.mkdir(exist_ok=True)
    
    # Salvar figura
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"💾 Figura salva: {output_path}")
    
    # Mostrar figura
    plt.show()
    
    return fig, ax


def main():
    """
    Função principal
    """
    logger.info("=" * 60)
    logger.info("🗺️  PLOTAGEM DE TRAJETÓRIAS - CICLONE AKARÁ 🌊")
    logger.info("=" * 60)
    logger.info("")
    
    # Carregar dados
    satellite_data = load_satellite_data()
    
    if not satellite_data:
        logger.error("❌ Nenhum dado encontrado! Execute primeiro download_satellite_data.py")
        logger.info("\n💡 Dica: Execute o download com:")
        logger.info("   python scripts/download_satellite_data.py")
        return
    
    logger.info(f"\n📊 Total de satélites com dados: {len(satellite_data)}")
    logger.info("")
    
    # Plotar trajetórias
    plot_satellite_tracks(satellite_data)
    
    # Fechar datasets
    # (Não necessário para dataframes)
    
    logger.info("")
    logger.info("🎉 Processamento concluído! 🚀")


if __name__ == "__main__":
    main()
