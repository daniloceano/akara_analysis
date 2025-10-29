#!/usr/bin/env python3
"""
Script para baixar e processar dados de ondas do ERA5.
Usa dados reais do Copernicus Climate Data Store (CDS) para análise oceânica.

ERA5 fornece dados de ondas incluindo:
- Altura significativa de ondas (swh)
- Direção média das ondas (mwd)
- Período médio das ondas (mwp)
- Período de pico das ondas (pp1d)

Dataset: ERA5 hourly data on single levels
Resolução: 0.25° (~28 km), dados horários
Fonte: Copernicus Climate Data Store (CDS)

Author: Danilo Couto de Souza
Date: October 2025
Project: Akará Cyclone Analysis
"""

import os
import sys
import subprocess
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Import configuration
try:
    from config import START_DATE, END_DATE, BBOX
except ImportError:
    print("❌ Erro: arquivo config.py não encontrado")
    print("💡 Copie config.py.template para config.py e configure suas credenciais")
    sys.exit(1)
try:
    import cdsapi
except ImportError:
    print("❌ cdsapi não instalado. Instalando...")
    subprocess.run([sys.executable, "-m", "pip", "install", "cdsapi"])
    import cdsapi

class ERA5WaveDownloader:
    """Classe para baixar dados de ondas do ERA5 via CDS API."""
    
    def __init__(self, output_dir):
        """
        Inicializar downloader ERA5.
        
        Args:
            output_dir: Diretório para salvar os dados
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar cliente CDS
        try:
            self.client = cdsapi.Client()
        except Exception as e:
            print(f"❌ Erro ao conectar com CDS: {e}")
            print("💡 Configure suas credenciais CDS em ~/.cdsapirc")
            raise
        
        # Região de interesse (do config.py)
        self.region = {
            'north': BBOX['north'],
            'south': BBOX['south'],
            'west': BBOX['west'],
            'east': BBOX['east']
        }
        
        # Variáveis de ondas disponíveis no ERA5
        self.variables = [
            'significant_height_of_combined_wind_waves_and_swell',
            'mean_wave_direction',
            'mean_wave_period',
            'peak_wave_period'
        ]

    def download_era5_waves(self, start_date, end_date):
        """
        Baixar dados de ondas do ERA5.
        
        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            
        Returns:
            xarray.Dataset ou None se erro
        """
        try:
            # Nome do arquivo
            output_file = self.output_dir / f"era5_waves_akara_{start_date.replace('-', '')}_{end_date.replace('-', '')}.nc"
            
            # Verificar se arquivo já existe
            if output_file.exists():
                print(f"📁 Arquivo já existe: {output_file}")
                print("📂 Carregando dados existentes...")
                ds = xr.open_dataset(output_file)
                print("✅ Dados ERA5 carregados com sucesso!")
                print(f"📊 Dimensões: {dict(ds.sizes)}")
                print(f"📋 Variáveis: {list(ds.data_vars.keys())}")
                return ds
            
            # Converter datas
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Gerar lista de anos e meses
            dates = pd.date_range(start_dt, end_dt, freq='D')
            years = sorted(list(set(dates.year)))
            months = sorted(list(set(dates.month)))
            days = sorted(list(set(dates.day)))
            
            print(f"🌊 Baixando dados ERA5: {start_date} a {end_date}")
            print(f"📅 Período: {start_dt.strftime('%Y-%m-%d')} a {end_dt.strftime('%Y-%m-%d')}")
            print(f"💾 Arquivo de saída: {output_file}")
            
            print("🚀 Executando download...")
            
            # Request para CDS
            request = {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': self.variables,
                'year': [str(y) for y in years],
                'month': [f'{m:02d}' for m in months],
                'day': [f'{d:02d}' for d in days],
                'time': [
                    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
                ],
                'area': [self.region['north'], self.region['west'], 
                        self.region['south'], self.region['east']]
            }
            
            # Download
            self.client.retrieve('reanalysis-era5-single-levels', request, str(output_file))
            
            # Carregar dados
            print("📂 Carregando dados...")
            ds = xr.open_dataset(output_file)
            
            print("✅ Download ERA5 concluído com sucesso!")
            return ds
            
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return None

    def create_quick_preview(self, ds):
        """Cria uma prévia rápida dos dados ERA5."""
        print("🎨 Criando prévia dos dados ERA5...")
        
        try:
            # Detectar variável de tempo
            time_var = 'valid_time' if 'valid_time' in ds.dims else 'time'
            
            # Selecionar timestep no meio do período
            mid_time = ds[time_var][len(ds[time_var])//2]
            data_slice = ds.sel({time_var: mid_time})
            
            # Criar figura
            fig, axes = plt.subplots(2, 2, figsize=(15, 10), 
                                    subplot_kw={'projection': ccrs.PlateCarree()})
            axes = axes.flatten()
            
            # Usar nomes das variáveis do ERA5
            variables = ['swh', 'mwd', 'mwp', 'pp1d']
            titles = ['Altura Significativa de Ondas (m)', 'Direção Média das Ondas (°)', 
                     'Período Médio (s)', 'Período de Pico (s)']
            cmaps = ['viridis', 'hsv', 'cividis', 'plasma']
            
            for i, (var, title, cmap) in enumerate(zip(variables, titles, cmaps)):
                ax = axes[i]
                
                # Adicionar características geográficas
                ax.add_feature(cfeature.COASTLINE)
                ax.add_feature(cfeature.BORDERS)
                ax.add_feature(cfeature.OCEAN, alpha=0.3)
                ax.add_feature(cfeature.LAND, alpha=0.5)
                
                # Plot dos dados
                if var in data_slice:
                    im = ax.contourf(data_slice.longitude, data_slice.latitude, 
                                   data_slice[var], levels=20, cmap=cmap, 
                                   transform=ccrs.PlateCarree())
                    
                    # Adicionar colorbar
                    plt.colorbar(im, ax=ax, shrink=0.7)
                else:
                    ax.text(0.5, 0.5, f'Variável {var}\\nnão encontrada', 
                           transform=ax.transAxes, ha='center', va='center')
                
                ax.set_title(title)
                ax.set_global()
                ax.gridlines(draw_labels=True, alpha=0.3)
            
            plt.tight_layout()
            
            # Salvar figura
            preview_file = self.output_dir / 'era5_waves_preview.png'
            plt.savefig(preview_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Preview salvo em: {preview_file}")
            
        except Exception as e:
            print(f"⚠️ Erro ao criar preview: {e}")

def main():
    """Função principal para download de dados ERA5."""
    print("=" * 60)
    print("🌊 DOWNLOAD E PROCESSAMENTO DOS DADOS ERA5 WAVES")
    print("=" * 60)
    print()
    
    # Diretório de saída
    base_dir = Path(__file__).parent.parent
    era5_dir = base_dir / 'data' / 'era5_waves'
    
    print(f"🌊 Configurado ERA5 Wave Downloader")
    print(f"📁 Diretório de saída: {era5_dir}")
    
    # Criar downloader
    downloader = ERA5WaveDownloader(era5_dir)
    
    print(f"🌍 Região: {downloader.region}")
    print(f"📊 Variáveis: {len(downloader.variables)} selecionadas")
    print()
    
    # Baixar dados para o período configurado (do config.py)
    print(f"📅 Período configurado: {START_DATE} a {END_DATE}")
    print(f"🌍 Região configurada: {BBOX}")
    print()
    
    ds = downloader.download_era5_waves(START_DATE, END_DATE)
    
    if ds is not None:
        print()
        print(f"📊 RESUMO DOS DADOS ERA5:")
        
        # Detectar variável de tempo correta
        time_var = None
        if 'time' in ds.dims:
            time_var = 'time'
        elif 'valid_time' in ds.dims:
            time_var = 'valid_time'
        
        if time_var:
            print(f"🗓️ Período: {ds[time_var].min().dt.strftime('%Y-%m-%d').values} a {ds[time_var].max().dt.strftime('%Y-%m-%d').values}")
        else:
            print(f"🗓️ Período: conforme solicitado ({START_DATE} a {END_DATE})")
            
        print(f"🌍 Dimensões: {dict(ds.sizes)}")
        print(f"📋 Variáveis: {list(ds.data_vars.keys())}")
        
        # Criar prévia
        downloader.create_quick_preview(ds)
        
        print()
        print("=" * 60)
        print("✅ Download de dados ERA5 concluído!")
        print("=" * 60)
        print()
        print("� Próximos passos:")
        print("   - Visualizar preview: data/era5_waves/era5_waves_preview.png")
        print("   - Criar animações: python scripts/create_wave_animations.py")
        print("   - Comparar com boias: python scripts/compare_buoy_locations.py")
    else:
        print()
        print("=" * 60)
        print("❌ FALHA no download dos dados ERA5")
        print("=" * 60)
        print()
        print("💡 Verifique suas credenciais do Copernicus CDS")
        print("💡 Configure ~/.cdsapirc com sua API key do CDS")
        print("💡 Registre-se em: https://cds.climate.copernicus.eu/")
        sys.exit(1)

if __name__ == "__main__":
    main()