#!/usr/bin/env python3
"""
Script exemplo demonstrando como usar os scripts de download
Este script executa todo o fluxo: setup -> download -> verificação

Autor: Danilo Couto de Souza
Data: Setembro 2025
"""

import subprocess
import sys
from pathlib import Path

def run_setup():
    """Executa o script de configuração."""
    print("1. Executando configuração inicial...")
    script_path = Path(__file__).parent / "setup_credentials.py"
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        print("✓ Configuração concluída")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro na configuração: {e}")
        return False

def run_download():
    """Executa o script de download."""
    print("\n2. Executando download dos dados...")
    script_path = Path(__file__).parent / "download_swot_data.py"
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        print("✓ Download concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro no download: {e}")
        return False

def check_downloaded_data():
    """Verifica os dados baixados."""
    print("\n3. Verificando dados baixados...")
    
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    
    if not data_dir.exists():
        print("✗ Diretório de dados não encontrado")
        return False
    
    total_files = 0
    total_size = 0
    
    for dataset_dir in data_dir.iterdir():
        if dataset_dir.is_dir():
            files = list(dataset_dir.glob("*"))
            file_count = len(files)
            
            dir_size = sum(f.stat().st_size for f in files if f.is_file())
            total_files += file_count
            total_size += dir_size
            
            print(f"  {dataset_dir.name}: {file_count} arquivos ({dir_size / 1024**2:.1f} MB)")
    
    print(f"\nTotal: {total_files} arquivos ({total_size / 1024**2:.1f} MB)")
    
    if total_files > 0:
        print("✓ Dados encontrados")
        return True
    else:
        print("✗ Nenhum arquivo encontrado")
        return False

def main():
    """Função principal."""
    print("SWOT Data Download - Execução Completa")
    print("======================================")
    print("Este script irá:")
    print("1. Configurar credenciais NASA Earthdata")
    print("2. Baixar dados SWOT para o ciclone Akará")
    print("3. Verificar os dados baixados")
    print()
    
    response = input("Continuar? (y/N): ")
    if response.lower() != 'y':
        print("Operação cancelada.")
        return
    
    # Executar fluxo completo
    success_setup = run_setup()
    if not success_setup:
        print("Falha na configuração. Abortando.")
        return
    
    success_download = run_download()
    if not success_download:
        print("Falha no download. Verificando dados existentes...")
    
    check_downloaded_data()
    
    print("\nFluxo de download concluído!")
    print("Próximos passos:")
    print("- Verificar os dados em: data/raw/")
    print("- Executar scripts de processamento")
    print("- Criar visualizações")

if __name__ == "__main__":
    main()