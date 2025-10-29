#!/usr/bin/env python3
"""
Script para download de dados SWOT para análise do ciclone Akará
Período: 14 a 22 de fevereiro de 2024
Autor: Danilo Couto de Souza
Data: Setembro 2025

Requer: podaac-data-subscriber
Instalação: conda install -c conda-forge podaac-data-subscriber

Uso:
    python download_swot_data.py
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configurações
START_DATE = "2024-02-14"
END_DATE = "2024-02-22"

# Região de interesse (Atlântico Sul - aproximada para o ciclone Akará)
# Expandida para garantir cobertura completa
BBOX = {
    'south': -45.0,   # Latitude sul
    'north': -15.0,   # Latitude norte  
    'west': -50.0,    # Longitude oeste
    'east': -20.0     # Longitude leste
}

# Datasets SWOT de interesse
DATASETS = {
    'SWOT_L2_LR_SSH_Basic_2.0': {
        'description': 'SWOT Level 2 Low Rate Sea Surface Height Basic',
        'variables': ['ssh_karin', 'sig0_karin', 'wind_speed_karin']
    },
    'SWOT_L2_LR_SSH_WINDWAVE_2.0': {
        'description': 'SWOT Level 2 Low Rate Sea Surface Height WindWave (with SWH)',
        'variables': ['swh_karin', 'wind_speed_karin', 'sig0_karin']
    },
    'SWOT_L2_HR_RiverSP_2.0': {
        'description': 'SWOT Level 2 High Rate River Single Pass',
        'variables': ['wse', 'width', 'slope']
    }
}

# Diretórios
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

def check_podaac_installation():
    """Verifica se o podaac-data-subscriber está instalado."""
    try:
        result = subprocess.run(['podaac-data-subscriber', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ podaac-data-subscriber encontrado: {result.stdout.strip()}")
            return True
        else:
            print("✗ Erro ao verificar versão do podaac-data-subscriber")
            return False
    except FileNotFoundError:
        print("✗ podaac-data-subscriber não encontrado")
        print("Instale com: conda install -c conda-forge podaac-data-subscriber")
        return False

def check_earthdata_credentials():
    """Verifica se as credenciais da NASA Earthdata estão configuradas."""
    netrc_file = Path.home() / '.netrc'
    earthdata_file = Path.home() / '.urs_cookies'
    
    if netrc_file.exists():
        print("✓ Arquivo .netrc encontrado")
        return True
    elif earthdata_file.exists():
        print("✓ Arquivo .urs_cookies encontrado")
        return True
    else:
        print("✗ Credenciais NASA Earthdata não encontradas")
        print("Configure suas credenciais:")
        print("1. Crie uma conta em: https://urs.earthdata.nasa.gov/")
        print("2. Execute: podaac-data-subscriber --help")
        print("3. Ou crie um arquivo .netrc manualmente")
        return False

def create_download_directories():
    """Cria diretórios necessários para download."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    for dataset_id in DATASETS.keys():
        dataset_dir = RAW_DATA_DIR / dataset_id
        dataset_dir.mkdir(exist_ok=True)
        print(f"✓ Diretório criado: {dataset_dir}")

def build_download_command(dataset_id, output_dir):
    """Constrói o comando de download para um dataset específico."""
    bbox_string = f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}"
    cmd = [
        'podaac-data-subscriber',
        '-c', dataset_id,
        '-d', output_dir,
        '--start-date', f"{START_DATE}T00:00:00Z",
        '--end-date', f"{END_DATE}T23:59:59Z",
        f'-b={bbox_string}',  # Usar sintaxe -b=valor para evitar problemas de parsing
        '-f'  # Force download (sobrescrever arquivos existentes)
    ]
    
    return cmd

def download_dataset(dataset_id, dataset_info):
    """Baixa um dataset específico."""
    print(f"\n{'='*60}")
    print(f"Baixando: {dataset_info['description']}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Período: {START_DATE} a {END_DATE}")
    print(f"Região: {BBOX}")
    print(f"{'='*60}")
    
    output_dir = RAW_DATA_DIR / dataset_id
    cmd = build_download_command(dataset_id, str(output_dir))
    
    print(f"Comando: {' '.join(cmd)}")
    print("\nIniciando download...")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✓ Download concluído para {dataset_id}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro no download de {dataset_id}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n✗ Download interrompido pelo usuário para {dataset_id}")
        return False

def main():
    """Função principal."""
    print("SWOT Data Downloader - Ciclone Akará")
    print("====================================")
    print(f"Período: {START_DATE} a {END_DATE}")
    print(f"Região: Atlântico Sul {BBOX}")
    print()
    
    # Verificações preliminares
    if not check_podaac_installation():
        sys.exit(1)
    
    if not check_earthdata_credentials():
        print("\nPrimeiro configure suas credenciais e tente novamente.")
        sys.exit(1)
    
    # Criar diretórios
    create_download_directories()
    
    # Confirmar download
    print(f"\nDatasets a serem baixados:")
    for i, (dataset_id, info) in enumerate(DATASETS.items(), 1):
        print(f"{i}. {dataset_id} - {info['description']}")
    
    response = input(f"\nIniciar download de {len(DATASETS)} datasets? (y/N): ")
    if response.lower() != 'y':
        print("Download cancelado.")
        sys.exit(0)
    
    # Download dos datasets
    successful_downloads = 0
    failed_downloads = 0
    
    for dataset_id, dataset_info in DATASETS.items():
        success = download_dataset(dataset_id, dataset_info)
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    # Resumo final
    print(f"\n{'='*60}")
    print("RESUMO DO DOWNLOAD")
    print(f"{'='*60}")
    print(f"✓ Downloads bem-sucedidos: {successful_downloads}")
    print(f"✗ Downloads falharam: {failed_downloads}")
    print(f"Total de datasets: {len(DATASETS)}")
    
    if failed_downloads > 0:
        print("\nAlguns downloads falharam. Verifique:")
        print("- Conexão com a internet")
        print("- Credenciais NASA Earthdata")
        print("- Disponibilidade dos dados para o período solicitado")
    
    print(f"\nDados salvos em: {RAW_DATA_DIR}")
    print("Download concluído!")

if __name__ == "__main__":
    main()