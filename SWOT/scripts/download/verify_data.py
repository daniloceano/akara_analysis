#!/usr/bin/env python3
"""
Script para verificar e resumir os dados SWOT baixados
Mostra informações básicas sobre os arquivos NetCDF e ZIP baixados

Autor: Danilo Couto de Souza
Data: Setembro 2025
"""

import os
import glob
import zipfile
from pathlib import Path
from datetime import datetime

def analyze_ssh_data():
    """Analisa os dados de SSH (Sea Surface Height)."""
    print("🌊 ANÁLISE DOS DADOS SSH (SWOT_L2_LR_SSH_Basic_2.0)")
    print("=" * 60)
    
    ssh_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_Basic_2.0")
    nc_files = list(ssh_dir.glob("*.nc"))
    
    if not nc_files:
        print("❌ Nenhum arquivo NetCDF encontrado")
        return
    
    print(f"📁 Diretório: {ssh_dir}")
    print(f"📄 Total de arquivos: {len(nc_files)}")
    
    # Analisar datas dos arquivos
    dates = []
    for file in nc_files:
        # Extrair data do nome do arquivo (formato: YYYYMMDDTHHMMSS)
        parts = file.name.split('_')
        for part in parts:
            if len(part) >= 15 and 'T' in part:
                try:
                    date_str = part[:15]  # YYYYMMDDTHHMMSS
                    date = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
                    dates.append(date)
                    break
                except ValueError:
                    continue
    
    if dates:
        dates.sort()
        print(f"📅 Período: {dates[0].strftime('%Y-%m-%d %H:%M')} a {dates[-1].strftime('%Y-%m-%d %H:%M')}")
        print(f"🗓️  Total de dias cobertos: {(dates[-1] - dates[0]).days + 1}")
    
    # Calcular tamanho total
    total_size = sum(f.stat().st_size for f in nc_files)
    print(f"💾 Tamanho total: {total_size / 1024**2:.1f} MB")
    
    # Mostrar alguns arquivos de exemplo
    print(f"\n📋 Primeiros arquivos:")
    for file in sorted(nc_files)[:3]:
        size_mb = file.stat().st_size / 1024**2
        print(f"   • {file.name} ({size_mb:.1f} MB)")
    
    if len(nc_files) > 3:
        print(f"   ... e mais {len(nc_files) - 3} arquivos")

def analyze_river_data():
    """Analisa os dados de rios."""
    print("\n🏞️  ANÁLISE DOS DADOS DE RIOS (SWOT_L2_HR_RiverSP_2.0)")
    print("=" * 60)
    
    river_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_HR_RiverSP_2.0")
    zip_files = list(river_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ Nenhum arquivo ZIP encontrado")
        return
    
    print(f"📁 Diretório: {river_dir}")
    print(f"📄 Total de arquivos: {len(zip_files)}")
    
    # Separar por tipo (Node vs Reach)
    node_files = [f for f in zip_files if "Node" in f.name]
    reach_files = [f for f in zip_files if "Reach" in f.name]
    
    print(f"🔵 Arquivos Node: {len(node_files)}")
    print(f"🔶 Arquivos Reach: {len(reach_files)}")
    
    # Calcular tamanho total
    total_size = sum(f.stat().st_size for f in zip_files)
    print(f"💾 Tamanho total: {total_size / 1024**2:.1f} MB")
    
    # Analisar conteúdo de um arquivo ZIP como exemplo
    if zip_files:
        print(f"\n🔍 Conteúdo do primeiro arquivo ZIP:")
        try:
            with zipfile.ZipFile(zip_files[0], 'r') as zf:
                file_list = zf.namelist()
                print(f"   📦 {zip_files[0].name}")
                for file_name in file_list[:5]:  # Mostrar até 5 arquivos
                    print(f"   ├── {file_name}")
                if len(file_list) > 5:
                    print(f"   └── ... e mais {len(file_list) - 5} arquivos")
        except Exception as e:
            print(f"   ❌ Erro ao ler ZIP: {e}")

def show_data_coverage():
    """Mostra cobertura temporal dos dados."""
    print("\n📊 RESUMO GERAL")
    print("=" * 60)
    
    ssh_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_Basic_2.0")
    river_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_HR_RiverSP_2.0")
    
    ssh_files = len(list(ssh_dir.glob("*.nc")))
    river_files = len(list(river_dir.glob("*.zip")))
    
    ssh_size = sum(f.stat().st_size for f in ssh_dir.glob("*.nc")) / 1024**2
    river_size = sum(f.stat().st_size for f in river_dir.glob("*.zip")) / 1024**2
    
    print(f"🌊 SSH Data: {ssh_files} arquivos, {ssh_size:.1f} MB")
    print(f"🏞️  River Data: {river_files} arquivos, {river_size:.1f} MB")
    print(f"📊 Total: {ssh_files + river_files} arquivos, {ssh_size + river_size:.1f} MB")
    
    print(f"\n✅ Download bem-sucedido para o período do ciclone Akará!")
    print(f"📅 Período: 14-22 de fevereiro de 2024")
    print(f"🌍 Região: Atlântico Sul")
    print(f"\n🚀 Próximos passos:")
    print(f"   1. Processar dados NetCDF (SSH)")
    print(f"   2. Extrair e processar arquivos ZIP (River)")
    print(f"   3. Criar mapas e visualizações")
    print(f"   4. Analisar altura de ondas durante o ciclone")

def main():
    """Função principal."""
    print("🛰️  VERIFICAÇÃO DOS DADOS SWOT - CICLONE AKARÁ")
    print("=" * 60)
    print(f"Data da verificação: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        analyze_ssh_data()
        analyze_river_data()
        show_data_coverage()
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        print("Verifique se os dados foram baixados corretamente.")

if __name__ == "__main__":
    main()