#!/usr/bin/env python3
"""
Script rápido para criar o dataset gridded a partir dos dados já processados
"""

import pickle
from pathlib import Path
import sys
import os

# Adicionar diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.processing.process_ssh_data import SWOTSSHProcessor

def main():
    print("🗃️ CRIANDO DATASET GRIDDED DOS DADOS SSH")
    print("=" * 50)
    
    # Carregar dados processados
    processed_file = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed/swot_ssh_processed.pkl")
    
    if not processed_file.exists():
        print("❌ Arquivo de dados processados não encontrado!")
        return
    
    print(f"📂 Carregando dados de: {processed_file}")
    with open(processed_file, 'rb') as f:
        processed_data = pickle.load(f)
    
    print(f"📊 {len(processed_data)} arquivos carregados")
    
    # Criar processador
    processor = SWOTSSHProcessor()
    
    # Criar dataset gridded
    print("🗃️ Criando dataset gridded...")
    gridded_ds = processor.create_gridded_dataset(processed_data)
    
    if gridded_ds is not None:
        # Salvar dataset gridded
        gridded_file = processed_file.parent / "swot_ssh_gridded.nc"
        gridded_ds.to_netcdf(gridded_file)
        print(f"💾 Dataset gridded salvo em: {gridded_file}")
        
        print("\n📊 RESUMO DO DATASET GRIDDED:")
        print(f"🌍 Dimensões: {dict(gridded_ds.dims)}")
        print(f"📋 Variáveis: {list(gridded_ds.data_vars)}")
        if gridded_ds.time.size > 0:
            try:
                print(f"📅 Período: {gridded_ds.time.min().values} a {gridded_ds.time.max().values}")
            except:
                print(f"📅 Período: {len(gridded_ds.time)} tempos")
        else:
            print(f"📅 Período: Sem dados de tempo válidos")
        
        print("\n✅ Dataset gridded criado com sucesso!")
        print("🚀 Agora você pode executar os scripts de visualização")
    else:
        print("❌ Falha na criação do dataset gridded")

if __name__ == "__main__":
    main()