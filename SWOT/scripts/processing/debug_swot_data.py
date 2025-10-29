#!/usr/bin/env python3
"""
🔍 Script de debug para entender a estrutura dos dados SWOT
"""

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path

def debug_swot_file():
    """Debug de um arquivo SWOT"""
    
    data_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_Basic_2.0")
    files = sorted(list(data_dir.glob("*.nc")))
    
    if not files:
        print("❌ Nenhum arquivo NetCDF encontrado!")
        return
    
    print(f"🔍 ANALISANDO ARQUIVO: {files[0].name}")
    print("=" * 80)
    
    try:
        # Carregar o arquivo
        ds = xr.open_dataset(files[0])
        
        print("📊 INFORMAÇÕES GERAIS:")
        print(f"   Dimensões: {dict(ds.dims)}")
        print(f"   Coordenadas: {list(ds.coords)}")
        print(f"   Variáveis de dados: {list(ds.data_vars)}")
        print()
        
        # Examinar algumas variáveis importantes
        for var in ['longitude', 'latitude', 'ssh_karin', 'ssh_karin_qual']:
            if var in ds:
                print(f"📋 VARIÁVEL '{var}':")
                data = ds[var]
                print(f"   Forma: {data.shape}")
                print(f"   Dimensões: {data.dims}")
                print(f"   Tipo: {data.dtype}")
                if hasattr(data, 'values'):
                    values = data.values
                    print(f"   Valores únicos: {np.unique(values).shape[0]} (de {values.size} total)")
                    if values.size > 0:
                        print(f"   Min/Max: {np.nanmin(values):.3f} / {np.nanmax(values):.3f}")
                        print(f"   NaNs: {np.isnan(values).sum()} ({100*np.isnan(values).mean():.1f}%)")
                print()
        
        # Verificar dados na região de interesse
        print("🌍 DADOS NA REGIÃO DE INTERESSE:")
        region = (-45, -15, -35, -5)  # lon_min, lon_max, lat_min, lat_max
        
        lon = ds['longitude'].values
        lat = ds['latitude'].values
        
        print(f"   Longitude: {lon.shape}, {np.nanmin(lon):.2f} a {np.nanmax(lon):.2f}")
        print(f"   Latitude: {lat.shape}, {np.nanmin(lat):.2f} a {np.nanmax(lat):.2f}")
        
        # Verificar se há dados na região
        if lon.size > 0 and lat.size > 0:
            lon_flat = lon.flatten()
            lat_flat = lat.flatten()
            
            mask = ((lon_flat >= region[0]) & (lon_flat <= region[1]) & 
                   (lat_flat >= region[2]) & (lat_flat <= region[3]) &
                   ~np.isnan(lon_flat) & ~np.isnan(lat_flat))
            
            print(f"   Pontos na região: {mask.sum()} de {mask.size}")
            
            if mask.sum() > 0:
                print(f"   Lon na região: {lon_flat[mask].min():.2f} a {lon_flat[mask].max():.2f}")
                print(f"   Lat na região: {lat_flat[mask].min():.2f} a {lat_flat[mask].max():.2f}")
        
        print()
        
        # Examinar a estrutura de tempo
        if 'time' in ds:
            print("⏰ INFORMAÇÕES DE TEMPO:")
            time_data = ds['time']
            print(f"   Forma: {time_data.shape}")
            print(f"   Dimensões: {time_data.dims}")
            if time_data.size > 0:
                time_values = pd.to_datetime(time_data.values)
                print(f"   Primeiro: {time_values.min()}")
                print(f"   Último: {time_values.max()}")
            print()
        
        # Examinar qualidade dos dados
        if 'ssh_karin_qual' in ds:
            print("✅ QUALIDADE DOS DADOS:")
            qual = ds['ssh_karin_qual'].values
            unique_vals = np.unique(qual[~np.isnan(qual)])
            print(f"   Valores de qualidade únicos: {unique_vals}")
            for val in unique_vals:
                count = (qual == val).sum()
                percent = 100 * count / qual.size
                print(f"   Qualidade {val}: {count} pontos ({percent:.1f}%)")
            print()
        
        ds.close()
        
    except Exception as e:
        print(f"❌ Erro ao analisar o arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_swot_file()