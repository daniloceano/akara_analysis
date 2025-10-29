#!/usr/bin/env python3
"""
Script para debugar o problema de timestamps nos dados SWOT processados.
"""

import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path

def check_original_files():
    """Verifica timestamps nos arquivos originais."""
    print("🔍 Verificando timestamps nos arquivos originais...")
    
    data_dir = Path('/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_Basic_2.0')
    nc_files = list(data_dir.glob("*.nc"))
    
    if not nc_files:
        print("❌ Nenhum arquivo .nc encontrado!")
        return
    
    print(f"📁 Encontrados {len(nc_files)} arquivos")
    
    # Verificar alguns arquivos
    for i, file_path in enumerate(nc_files[:5]):  # Verificar apenas 5 primeiros
        print(f"\n📊 Arquivo {i+1}: {file_path.name}")
        try:
            with xr.open_dataset(file_path) as ds:
                if 'time' in ds:
                    time_values = ds.time.values
                    print(f"   Forma do tempo: {time_values.shape}")
                    print(f"   Tipo do tempo: {time_values.dtype}")
                    
                    # Verificar valores válidos
                    valid_times = time_values[~pd.isna(time_values)]
                    if len(valid_times) > 0:
                        print(f"   Primeiro tempo válido: {pd.to_datetime(valid_times[0])}")
                        print(f"   Último tempo válido: {pd.to_datetime(valid_times[-1])}")
                        print(f"   Tempos válidos: {len(valid_times)}/{len(time_values.flatten())}")
                    else:
                        print("   ❌ Nenhum tempo válido encontrado!")
                        
                    # Verificar atributos de tempo
                    if 'time_coverage_start' in ds.attrs:
                        print(f"   time_coverage_start: {ds.attrs['time_coverage_start']}")
                    if 'time_coverage_end' in ds.attrs:
                        print(f"   time_coverage_end: {ds.attrs['time_coverage_end']}")
                else:
                    print("   ❌ Variável 'time' não encontrada!")
                    
        except Exception as e:
            print(f"   ❌ Erro ao abrir arquivo: {e}")

def check_processed_file():
    """Verifica timestamps no arquivo processado."""
    print("\n🔍 Verificando timestamps no arquivo processado...")
    
    processed_file = Path('/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed/swot_ssh_gridded.nc')
    
    if not processed_file.exists():
        print("❌ Arquivo processado não encontrado!")
        return
    
    try:
        with xr.open_dataset(processed_file) as ds:
            print(f"📊 Dataset processado carregado")
            print(f"   Dimensões: {dict(ds.dims)}")
            
            if 'time' in ds:
                time_values = ds.time.values
                print(f"   Forma do tempo: {time_values.shape}")
                print(f"   Tipo do tempo: {time_values.dtype}")
                
                # Verificar se todos são NaT
                nat_count = pd.isna(time_values).sum()
                print(f"   Valores NaT: {nat_count}/{len(time_values)}")
                
                if nat_count < len(time_values):
                    valid_times = time_values[~pd.isna(time_values)]
                    print(f"   Primeiro tempo válido: {pd.to_datetime(valid_times[0])}")
                    print(f"   Último tempo válido: {pd.to_datetime(valid_times[-1])}")
                else:
                    print("   ❌ TODOS os timestamps são NaT!")
            else:
                print("   ❌ Variável 'time' não encontrada!")
                
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo processado: {e}")

def check_pickle_file():
    """Verifica timestamps no arquivo pickle."""
    print("\n🔍 Verificando timestamps no arquivo pickle...")
    
    pickle_file = Path('/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed/swot_ssh_processed.pkl')
    
    if not pickle_file.exists():
        print("❌ Arquivo pickle não encontrado!")
        return
    
    try:
        import pickle
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"📊 Dados pickle carregados: {len(data)} arquivos")
        
        # Verificar primeiro arquivo
        if data:
            first_file = data[0]
            print(f"   Primeiro arquivo: {first_file.get('file_name', 'unknown')}")
            
            if 'file_timestamp' in first_file:
                print(f"   file_timestamp: {first_file['file_timestamp']}")
            
            if 'time' in first_file:
                time_values = first_file['time']
                if hasattr(time_values, 'shape'):
                    print(f"   Forma do tempo: {time_values.shape}")
                    valid_times = time_values[~pd.isna(time_values)]
                    if len(valid_times) > 0:
                        print(f"   Primeiro tempo válido: {pd.to_datetime(valid_times[0])}")
                    else:
                        print("   ❌ Nenhum tempo válido no pickle!")
                        
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo pickle: {e}")

if __name__ == "__main__":
    print("🐛 DEBUG: Investigando problema de timestamps")
    print("=" * 60)
    
    check_original_files()
    check_processed_file()
    check_pickle_file()
    
    print("\n✅ Investigação concluída!")