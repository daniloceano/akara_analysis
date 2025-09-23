#!/usr/bin/env python3
"""
Script para testar os datasets SWOT e verificar disponibilidade
Executa busca dry-run para validar parâmetros antes do download real

Autor: Danilo Couto de Souza
Data: Setembro 2025
"""

import subprocess
import sys
from pathlib import Path

# Mesmas configurações do script principal
START_DATE = "2024-02-14T00:00:00Z"
END_DATE = "2024-02-22T23:59:59Z"
BBOX = "-50.0,-45.0,-20.0,-15.0"  # west,south,east,north

DATASETS = [
    'SWOT_L2_LR_SSH_Basic_2.0',
    'SWOT_L2_HR_RiverSP_2.0'
]

def test_dataset(dataset_id):
    """Testa um dataset específico com dry-run."""
    print(f"\n{'='*50}")
    print(f"Testando: {dataset_id}")
    print(f"{'='*50}")
    
    cmd = [
        'podaac-data-subscriber',
        '-c', dataset_id,
        '-d', '/tmp/test_swot',  # Diretório temporário
        '--start-date', START_DATE,
        '--end-date', END_DATE,
        f'-b={BBOX}',  # Usar sintaxe -b=valor
        '--dry-run',
        '--verbose'
    ]
    
    print(f"Comando: {' '.join(cmd)}")
    print("\nExecutando...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ Teste bem-sucedido!")
            print("Saída:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print("✗ Teste falhou")
            print("Erro:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ Timeout - teste demorou muito")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def main():
    """Função principal."""
    print("SWOT Dataset Tester")
    print("==================")
    print(f"Período: {START_DATE} a {END_DATE}")
    print(f"Região: {BBOX}")
    print()
    
    # Verificar se podaac-data-subscriber está disponível
    try:
        result = subprocess.run(['podaac-data-subscriber', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ podaac-data-subscriber: {result.stdout.strip()}")
        else:
            print("✗ Erro ao verificar podaac-data-subscriber")
            sys.exit(1)
    except FileNotFoundError:
        print("✗ podaac-data-subscriber não encontrado")
        print("Instale com: conda install -c conda-forge podaac-data-subscriber")
        sys.exit(1)
    
    # Testar cada dataset
    successful_tests = 0
    failed_tests = 0
    
    for dataset_id in DATASETS:
        success = test_dataset(dataset_id)
        if success:
            successful_tests += 1
        else:
            failed_tests += 1
    
    # Resumo
    print(f"\n{'='*50}")
    print("RESUMO DOS TESTES")
    print(f"{'='*50}")
    print(f"✓ Testes bem-sucedidos: {successful_tests}")
    print(f"✗ Testes falharam: {failed_tests}")
    print(f"Total de datasets: {len(DATASETS)}")
    
    if failed_tests > 0:
        print("\nAlguns testes falharam. Possíveis causas:")
        print("- Credenciais não configuradas")
        print("- Dataset não disponível para o período")
        print("- Problemas de conectividade")
        print("- Parâmetros incorretos")
    else:
        print("\n✓ Todos os testes passaram!")
        print("Você pode executar o download real com: python download_swot_data.py")

if __name__ == "__main__":
    main()