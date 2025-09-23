#!/usr/bin/env python3
"""
🔍 Script para investigar o problema das datas nos dados SWOT
"""

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

def investigate_time_issue():
    """Investiga o problema com as datas no dataset gridded"""
    
    print("🔍 INVESTIGANDO PROBLEMA DAS DATAS SWOT")
    print("=" * 50)
    
    # Carregar dataset gridded
    gridded_file = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed/swot_ssh_gridded.nc")
    
    if not gridded_file.exists():
        print("❌ Dataset gridded não encontrado!")
        return
    
    print(f"📂 Carregando: {gridded_file}")
    ds = xr.open_dataset(gridded_file)
    
    print(f"\n📊 INFORMAÇÕES DO DATASET:")
    print(f"🌍 Dimensões: {dict(ds.dims)}")
    print(f"📋 Variáveis: {list(ds.data_vars)}")
    print(f"📅 Coordenada tempo: {ds.time}")
    
    print(f"\n🕐 ANÁLISE DAS DATAS:")
    print(f"Tipo da coordenada tempo: {type(ds.time.values[0])}")
    print(f"Valores de tempo: {ds.time.values}")
    
    # Verificar dados originais
    print(f"\n📂 VERIFICANDO ARQUIVOS ORIGINAIS:")
    raw_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_Basic_2.0")
    
    if raw_dir.exists():
        files = sorted(list(raw_dir.glob("*.nc")))
        print(f"Encontrados {len(files)} arquivos originais")
        
        # Verificar primeiros arquivos
        for i, file in enumerate(files[:3]):
            print(f"\n📄 Arquivo {i+1}: {file.name}")
            try:
                ds_orig = xr.open_dataset(file)
                if 'time' in ds_orig:
                    time_vals = ds_orig.time.values
                    print(f"   Tempo original: {time_vals[:5]}...")
                    print(f"   Tipo: {type(time_vals[0])}")
                    if len(time_vals) > 0:
                        print(f"   Primeiro: {pd.to_datetime(time_vals[0])}")
                        print(f"   Último: {pd.to_datetime(time_vals[-1])}")
                ds_orig.close()
            except Exception as e:
                print(f"   ❌ Erro: {e}")
    
    ds.close()

if __name__ == "__main__":
    investigate_time_issue()