#!/usr/bin/env python3
"""
Script de teste para visualizar frames individuais antes de criar animação completa.
Gera imagens PNG de alguns timesteps para verificar se está tudo correto.
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import logging
import sys

# Adicionar path do script principal
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_preview_frames(n_frames=5):
    """Criar preview de alguns frames."""
    logger.info("=" * 60)
    logger.info("🎬 TESTE DE PREVIEW - Frames Individuais")
    logger.info("=" * 60)
    
    # Paths
    data_dir = PROJECT_ROOT / 'data'
    era5_file = PROJECT_ROOT / 'data' / 'era5_waves' / 'era5_waves_akara_20240216_20240220.nc'
    output_dir = PROJECT_ROOT / 'figures' / 'animation_preview'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar ERA5
    if not era5_file.exists():
        logger.error(f"❌ ERA5 não encontrado: {era5_file}")
        logger.info("💡 Execute: python scripts/download_era5_waves.py")
        return
    
    # Carregar ERA5
    logger.info("🌊 Carregando ERA5...")
    era5_ds = xr.open_dataset(era5_file)
    
    # Renomear se necessário
    if 'valid_time' in era5_ds.dims:
        era5_ds = era5_ds.rename({'valid_time': 'time'})
    
    # Detectar variável de onda
    if 'swh' in era5_ds.variables:
        wave_var = 'swh'
    elif 'significant_height_of_combined_wind_waves_and_swell' in era5_ds.variables:
        wave_var = 'significant_height_of_combined_wind_waves_and_swell'
    else:
        logger.error("❌ Variável de onda não encontrada")
        return
    
    logger.info(f"✅ ERA5 carregado: {len(era5_ds.time)} timesteps")
    logger.info(f"📊 Variável: {wave_var}")
    
    # Carregar um satélite (Jason-3 para teste)
    logger.info("🛰️ Carregando Jason-3...")
    jason_file = data_dir / 'Jason-3' / 'Jason-3_Akara_2024-02-14_2024-02-22.nc.csv'
    
    if jason_file.exists():
        df = pd.read_csv(jason_file)
        # Parse times as UTC-aware timestamps so they compare correctly
        # with ERA5 times (which we'll localize to UTC below if needed).
        df['time'] = pd.to_datetime(df['time'], utc=True)
        df_vavh = df[df['variable'] == 'VAVH'].copy()
        logger.info(f"✅ Jason-3: {len(df_vavh)} pontos")
    else:
        logger.warning("⚠️ Jason-3 não encontrado")
        df_vavh = pd.DataFrame()
    
    # Selecionar timesteps para preview
    total_times = len(era5_ds.time)
    indices = np.linspace(0, total_times-1, min(n_frames, total_times), dtype=int)
    
    logger.info(f"🎨 Criando {len(indices)} frames de preview...")
    
    # Criar frames
    for i, time_idx in enumerate(indices):
        current_time = pd.to_datetime(era5_ds.time.values[time_idx])
        # Ensure ERA5 time is timezone-aware UTC so comparisons with
        # satellite UTC timestamps succeed. Localize only if tz-naive.
        if current_time.tzinfo is None:
            current_time = current_time.tz_localize('UTC')
        
        logger.info(f"  Frame {i+1}/{len(indices)}: {current_time}")
        
        # Criar figura
        fig = plt.figure(figsize=(14, 10), facecolor='white')
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Plot ERA5
        era5_data = era5_ds[wave_var].isel(time=time_idx)
        
        im = ax.contourf(
            era5_ds.longitude,
            era5_ds.latitude,
            era5_data,
            levels=20,
            cmap='viridis',
            vmin=0,
            vmax=8,
            transform=ccrs.PlateCarree(),
            alpha=0.8
        )
        
        plt.colorbar(im, ax=ax, label='Altura de Onda (m)', shrink=0.7)
        
        # Plot satélite (janela de ±30 min)
        if len(df_vavh) > 0:
            time_start = current_time - pd.Timedelta(minutes=30)
            time_end = current_time + pd.Timedelta(minutes=30)
            
            mask = (df_vavh['time'] >= time_start) & (df_vavh['time'] <= time_end)
            df_window = df_vavh[mask]
            
            if len(df_window) > 0:
                ax.scatter(
                    df_window['longitude'],
                    df_window['latitude'],
                    c=df_window['value'],
                    s=50,
                    cmap='viridis',
                    vmin=0,
                    vmax=8,
                    edgecolors='black',
                    linewidth=0.5,
                    transform=ccrs.PlateCarree(),
                    zorder=5,
                    label=f'Jason-3 ({len(df_window)} pts)'
                )
                ax.legend(loc='upper left', fontsize=10)
        
        # Features
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.COASTLINE, linewidth=1.0)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', alpha=0.5)
        
        # Extent
        ax.set_extent([-50, -20, -45, -15], crs=ccrs.PlateCarree())
        
        # Grid
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', 
                         alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        
        # Título
        ax.set_title(
            f'ERA5 + Jason-3 - {current_time.strftime("%Y-%m-%d %H:%M UTC")}',
            fontsize=14,
            fontweight='bold',
            pad=10
        )
        
        # Salvar
        output_file = output_dir / f'preview_frame_{i:03d}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"    💾 Salvo: {output_file.name}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ PREVIEW CONCLUÍDO!")
    logger.info("=" * 60)
    logger.info(f"📁 Frames salvos em: {output_dir}")
    logger.info("")
    logger.info("💡 Verifique os frames antes de criar animação completa:")
    logger.info(f"   open {output_dir}")


if __name__ == "__main__":
    test_preview_frames(n_frames=5)
