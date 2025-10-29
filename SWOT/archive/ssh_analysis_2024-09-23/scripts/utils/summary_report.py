#!/usr/bin/env python3
"""
Resumo das Visualizações Combinadas SWOT + ERA5
===============================================

Este script cria um relatório resumo de todas as visualizações geradas.
"""

import os
from pathlib import Path
from datetime import datetime

def create_summary_report():
    """
    Create a summary report of all generated visualizations
    """
    base_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT")
    figures_dir = base_dir / "figures"
    
    print("="*80)
    print("RELATÓRIO DE VISUALIZAÇÕES COMBINADAS SWOT + ERA5")
    print("="*80)
    print(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Combined visualizations
    combined_dir = figures_dir / "combined"
    if combined_dir.exists():
        print("📁 VISUALIZAÇÕES COMBINADAS:")
        print("-" * 40)
        
        # Check for main files
        gif_file = combined_dir / "combined_animation.gif"
        timeseries_file = combined_dir / "rio_timeseries_combined.png"
        spatial_file = combined_dir / "spatial_comparison_swot_era5.png"
        
        if gif_file.exists():
            size_mb = gif_file.stat().st_size / (1024*1024)
            print(f"🎬 GIF Animado: {gif_file.name} ({size_mb:.1f} MB)")
            
        if timeseries_file.exists():
            size_mb = timeseries_file.stat().st_size / (1024*1024)
            print(f"📊 Série Temporal Rio: {timeseries_file.name} ({size_mb:.1f} MB)")
            
        if spatial_file.exists():
            size_mb = spatial_file.stat().st_size / (1024*1024)
            print(f"🗺️  Comparação Espacial: {spatial_file.name} ({size_mb:.1f} MB)")
        
        # Check snapshots
        snapshots_dir = combined_dir / "snapshots"
        if snapshots_dir.exists():
            snapshots = list(snapshots_dir.glob("*.png"))
            if snapshots:
                total_size = sum(f.stat().st_size for f in snapshots) / (1024*1024)
                print(f"📸 Snapshots: {len(snapshots)} arquivos ({total_size:.1f} MB total)")
                print(f"   Período: {snapshots[0].name[17:25]} a {snapshots[-1].name[17:25]}")
        print()
    
    # SWOT only visualizations
    swot_dir = figures_dir / "swot_only"
    if swot_dir.exists():
        print("📁 VISUALIZAÇÕES SOMENTE SWOT:")
        print("-" * 40)
        swot_files = list(swot_dir.glob("*.png")) + list(swot_dir.glob("*.gif"))
        for file in sorted(swot_files):
            size_mb = file.stat().st_size / (1024*1024)
            print(f"   {file.name} ({size_mb:.1f} MB)")
        print()
    
    # ERA5 only visualizations  
    era5_dir = figures_dir / "era5_only"
    if era5_dir.exists():
        print("📁 VISUALIZAÇÕES SOMENTE ERA5:")
        print("-" * 40)
        era5_files = list(era5_dir.glob("*.png"))
        for file in sorted(era5_files):
            size_mb = file.stat().st_size / (1024*1024)
            print(f"   {file.name} ({size_mb:.1f} MB)")
        print()
    
    # Data summary
    print("📊 RESUMO DOS DADOS:")
    print("-" * 40)
    
    data_dir = base_dir / "data"
    
    # SWOT data
    swot_processed = data_dir / "processed" / "swot_ssh_gridded.nc"
    if swot_processed.exists():
        size_mb = swot_processed.stat().st_size / (1024*1024)
        print(f"🛰️  SWOT Processado: {size_mb:.1f} MB")
        
    # ERA5 data
    era5_data = data_dir / "era5_waves"
    if era5_data.exists():
        era5_files = list(era5_data.glob("*.nc"))
        if era5_files:
            total_size = sum(f.stat().st_size for f in era5_files) / (1024*1024)
            print(f"🌊 ERA5 Ondas: {len(era5_files)} arquivos, {total_size:.1f} MB total")
    
    print()
    print("="*80)
    print("VISUALIZAÇÕES DISPONÍVEIS:")
    print("="*80)
    print("1. Snapshots Combinados (26 imagens): SSH SWOT + Ondas ERA5")
    print("2. GIF Animado: Evolução temporal completa")
    print("3. Série Temporal Rio de Janeiro: SSH com mapa de localização")
    print("4. Comparação Espacial: Análise correlação SWOT vs ERA5")
    print()
    print("📍 Todos os dados são REAIS (SWOT L3 + ERA5 Copernicus)")
    print("📅 Período: 14-22 Fevereiro 2024")
    print("🗺️  Região: Área Akará (Costa Brasileira)")
    print("⭐ Ponto de Interesse: Rio de Janeiro (-22.91°, -43.17°)")
    print("="*80)

if __name__ == "__main__":
    create_summary_report()