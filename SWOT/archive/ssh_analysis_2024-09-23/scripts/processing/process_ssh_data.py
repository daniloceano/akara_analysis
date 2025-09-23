#!/usr/bin/env python3
"""
Script para processamento dos dados SSH do SWOT
Carrega, processa e prepara dados para visualização

Autor: Danilo Couto de Souza
Data: Setembro 2025
Projeto: Análise SWOT - Ciclone Akará
"""

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SWOTSSHProcessor:
    """Classe para processamento dos dados SSH do SWOT."""
    
    def __init__(self, data_dir=None):
        """Inicializa o processador."""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "SWOT_L2_LR_SSH_Basic_2.0"
        else:
            self.data_dir = Path(data_dir)
        
        self.processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        print(f"📁 Diretório de dados: {self.data_dir}")
        print(f"💾 Diretório processado: {self.processed_dir}")
    
    def list_files(self):
        """Lista todos os arquivos NetCDF disponíveis."""
        nc_files = list(self.data_dir.glob("*.nc"))
        nc_files.sort()
        
        print(f"🔍 Encontrados {len(nc_files)} arquivos NetCDF")
        
        # Extrair informações temporais
        file_info = []
        for file in nc_files:
            try:
                # Extrair timestamp do nome do arquivo
                parts = file.name.split('_')
                for part in parts:
                    if len(part) >= 15 and 'T' in part:
                        date_str = part[:15]  # YYYYMMDDTHHMMSS
                        timestamp = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
                        file_info.append({
                            'file': file,
                            'timestamp': timestamp,
                            'date': timestamp.date(),
                            'size_mb': file.stat().st_size / 1024**2
                        })
                        break
            except Exception as e:
                print(f"⚠️ Erro ao processar {file.name}: {e}")
        
        # Criar DataFrame para análise
        df = pd.DataFrame(file_info)
        if not df.empty:
            df = df.sort_values('timestamp')
            print(f"📅 Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
            print(f"📊 Tamanho total: {df['size_mb'].sum():.1f} MB")
        
        return file_info
    
    def load_single_file(self, file_path, region_bounds=None):
        """
        Carrega um único arquivo NetCDF.
        
        Parameters:
        -----------
        file_path : Path
            Caminho para o arquivo NetCDF
        region_bounds : dict
            Limites da região {'lat_min': -45, 'lat_max': -15, 'lon_min': -50, 'lon_max': -20}
        """
        try:
            # Carregar arquivo
            ds = xr.open_dataset(file_path)
            
            print(f"📂 Carregando: {file_path.name}")
            print(f"🌍 Dimensões: {dict(ds.dims)}")
            print(f"📋 Variáveis principais: {list(ds.data_vars)[:10]}")
            
            # Filtrar por região se especificado
            if region_bounds:
                # Converter longitude de 0-360 para -180 a 180
                ds_lon_converted = xr.where(ds.longitude > 180, ds.longitude - 360, ds.longitude)
                ds = ds.assign_coords(longitude=ds_lon_converted)
                
                lat_mask = (ds.latitude >= region_bounds['lat_min']) & (ds.latitude <= region_bounds['lat_max'])
                lon_mask = (ds.longitude >= region_bounds['lon_min']) & (ds.longitude <= region_bounds['lon_max'])
                
                # Aplicar máscara apenas onde há dados válidos
                combined_mask = lat_mask & lon_mask
                valid_data = combined_mask.any()
                
                if valid_data:
                    ds = ds.where(combined_mask)
                    print(f"🎯 Filtrado para região: {region_bounds}")
                    
                    # Contar pontos válidos
                    valid_ssh = (~np.isnan(ds.ssh_karin)).sum()
                    print(f"📊 Pontos SSH válidos na região: {valid_ssh.values}")
                else:
                    print(f"⚠️  Nenhum dado encontrado na região especificada")
                    return None
            
            return ds
            
        except Exception as e:
            print(f"❌ Erro ao carregar {file_path}: {e}")
            return None
    
    def extract_time_from_filename(self, filename):
        """Extrai tempo do nome do arquivo SWOT como backup"""
        try:
            # Formato: SWOT_L2_LR_SSH_Basic_XXX_XXX_YYYYMMDDThhmmss_YYYYMMDDThhmmss_XXXX_XX.nc
            parts = filename.stem.split('_')
            if len(parts) >= 8:
                start_time_str = parts[6]  # YYYYMMDDThhmmss
                if len(start_time_str) == 15 and 'T' in start_time_str:
                    return pd.to_datetime(start_time_str, format='%Y%m%dT%H%M%S')
        except Exception as e:
            print(f"⚠️ Erro ao extrair tempo do nome do arquivo {filename}: {e}")
        return None
    
    def extract_ssh_data(self, ds, filename):
        """
        Extrai dados SSH relevantes de um dataset.
        
        Parameters:
        -----------
        ds : xarray.Dataset
            Dataset SWOT carregado
        filename : Path
            Caminho do arquivo para backup de tempo
        """
        try:
            # Extrair coordenadas e SSH
            data = {
                'longitude': ds.longitude.values,
                'latitude': ds.latitude.values,
                'ssh_karin': ds.ssh_karin.values,  # Altura da superfície do mar
                'ssh_karin_2': ds.ssh_karin_2.values if 'ssh_karin_2' in ds else None,
                'time': ds.time.values,
                'cycle_number': ds.cycle_number.values if 'cycle_number' in ds else None,
                'pass_number': ds.pass_number.values if 'pass_number' in ds else None,
            }
            
            # Adicionar qualidade se disponível
            if 'ssh_karin_qual' in ds:
                data['quality'] = ds.ssh_karin_qual.values
            
            # Adicionar informações do arquivo para debugging
            data['file_info'] = {
                'filename': str(ds.attrs.get('source_file', 'unknown')),
                'time_coverage_start': ds.attrs.get('time_coverage_start', ''),
                'time_coverage_end': ds.attrs.get('time_coverage_end', '')
            }
            
            # Adicionar SWH (altura significativa de ondas) se disponível
            if 'swh_karin' in ds:
                data['swh_karin'] = ds.swh_karin.values
                print("🌊 Dados de altura de ondas (SWH) encontrados!")
            
            # Adicionar wind speed se disponível
            if 'wind_speed_karin' in ds:
                data['wind_speed'] = ds.wind_speed_karin.values
                print("💨 Dados de velocidade do vento encontrados!")
            
            return data
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados SSH: {e}")
            return None
    
    def process_all_files(self, region_bounds=None, quality_filter=True):
        """
        Processa todos os arquivos SSH e combina em um dataset.
        
        Parameters:
        -----------
        region_bounds : dict
            Limites da região de interesse
        quality_filter : bool
            Se deve aplicar filtro de qualidade
        """
        print("🔄 Processando todos os arquivos SSH...")
        
        file_info = self.list_files()
        
        if not file_info:
            print("❌ Nenhum arquivo encontrado!")
            return None
        
        # Região padrão (Atlântico Sul - Ciclone Akará)
        if region_bounds is None:
            region_bounds = {
                'lat_min': -45.0,
                'lat_max': -15.0,
                'lon_min': -50.0,
                'lon_max': -20.0
            }
        
        processed_data = []
        
        for i, info in enumerate(file_info):
            print(f"\n📊 Processando {i+1}/{len(file_info)}: {info['file'].name}")
            
            # Carregar arquivo
            ds = self.load_single_file(info['file'], region_bounds)
            if ds is None:
                continue
            
            # Extrair dados SSH
            ssh_data = self.extract_ssh_data(ds, info['file'])
            if ssh_data is None:
                continue
            
            # Adicionar timestamp
            ssh_data['file_timestamp'] = info['timestamp']
            ssh_data['file_name'] = info['file'].name
            
            processed_data.append(ssh_data)
            
            # Fechar dataset para liberar memória
            ds.close()
        
        print(f"\n✅ Processamento concluído! {len(processed_data)} arquivos processados.")
        
        # Salvar dados processados
        output_file = self.processed_dir / "swot_ssh_processed.pkl"
        pd.to_pickle(processed_data, output_file)
        print(f"💾 Dados salvos em: {output_file}")
        
        return processed_data
    
    def create_gridded_dataset(self, data_list, resolution=0.05):
        """
        Cria um dataset gridded a partir dos dados processados.
        
        Parameters:
        -----------
        data_list : list
            Lista de dicionários com dados processados
        resolution : float
            Resolução da grade em graus (padrão: 0.05° ≈ 5.5 km)
        """
        if not data_list:
            print("❌ Nenhum dado para criar grade!")
            return None
        
        print(f"🗃️ Criando dataset gridded com resolução {resolution}°...")
        
        # Coletar todas as coordenadas válidas na região de interesse
        all_lons = []
        all_lats = []
        
        # Definir região do ciclone Akará
        akara_region = {'lon_min': -45, 'lon_max': -25, 'lat_min': -35, 'lat_max': -20}
        
        for data in data_list:
            if data and 'longitude' in data and 'latitude' in data:
                lons = data['longitude'].flatten()
                lats = data['latitude'].flatten()
                
                # Filtrar para região do ciclone
                mask = ((lons >= akara_region['lon_min']) & (lons <= akara_region['lon_max']) &
                       (lats >= akara_region['lat_min']) & (lats <= akara_region['lat_max']) &
                       ~np.isnan(lons) & ~np.isnan(lats))
                
                if np.any(mask):
                    all_lons.extend(lons[mask])
                    all_lats.extend(lats[mask])
        
        if not all_lons:
            print("❌ Nenhum dado válido encontrado na região do ciclone!")
            return None
        
        # Criar grade baseada nos dados disponíveis
        lon_min, lon_max = np.min(all_lons), np.max(all_lons)
        lat_min, lat_max = np.min(all_lats), np.max(all_lats)
        
        # Expandir um pouco os limites
        lon_buffer = (lon_max - lon_min) * 0.1
        lat_buffer = (lat_max - lat_min) * 0.1
        
        lon_grid = np.arange(lon_min - lon_buffer, lon_max + lon_buffer + resolution, resolution)
        lat_grid = np.arange(lat_min - lat_buffer, lat_max + lat_buffer + resolution, resolution)
        
        print(f"📏 Grade: {len(lon_grid)} x {len(lat_grid)} pontos")
        print(f"🌍 Região: {lon_min:.2f}°E a {lon_max:.2f}°E, {lat_min:.2f}°N a {lat_max:.2f}°N")
        
        # Inicializar arrays para variáveis
        variables = ['ssh_karin', 'quality']
        gridded_vars = {}
        
        for var in variables:
            if var == 'quality':
                gridded_vars[var] = np.full((len(data_list), len(lat_grid), len(lon_grid)), np.nan)
            else:
                gridded_vars[var] = np.full((len(data_list), len(lat_grid), len(lon_grid)), np.nan)
        
        # Coletar tempos
        times = []
        
        # Processar cada arquivo
        for t_idx, data in enumerate(data_list):
            if not data:
                continue
                
            print(f"🔄 Processando arquivo {t_idx+1}/{len(data_list)}...")
            
            lons = data['longitude'].flatten()
            lats = data['latitude'].flatten()
            
            # Adicionar tempo - usar o tempo médio do arquivo
            if 'time' in data and len(data['time']) > 0:
                time_values = data['time']
                # Encontrar primeiro tempo válido (não NaT)
                valid_times = [t for t in time_values.flatten() if not pd.isna(t)]
                if valid_times:
                    # Usar o tempo médio do arquivo
                    times.append(pd.to_datetime(valid_times[len(valid_times)//2]))
                else:
                    # Backup: usar timestamp do arquivo
                    if 'file_timestamp' in data:
                        times.append(data['file_timestamp'])
                    else:
                        times.append(pd.NaT)
            else:
                # Backup: usar timestamp do arquivo
                if 'file_timestamp' in data:
                    times.append(data['file_timestamp'])
                else:
                    times.append(pd.NaT)
                    
            # Processar cada variável
            for var in variables:
                if var in data and data[var] is not None:
                    values = data[var].flatten()
                    
                    # Aplicar binning simples
                    for i, (lon, lat, val) in enumerate(zip(lons, lats, values)):
                        if (np.isnan(lon) or np.isnan(lat) or np.isnan(val) or
                            lon < lon_grid[0] or lon > lon_grid[-1] or
                            lat < lat_grid[0] or lat > lat_grid[-1]):
                            continue
                        
                        # Encontrar índices da grade
                        lon_idx = np.argmin(np.abs(lon_grid - lon))
                        lat_idx = np.argmin(np.abs(lat_grid - lat))
                        
                        # Assignar valor (usar último valor se já existe)
                        gridded_vars[var][t_idx, lat_idx, lon_idx] = val
        
        # Criar dataset xarray
        data_vars = {}
        for var, values in gridded_vars.items():
            data_vars[var] = (['time', 'latitude', 'longitude'], values)
        
        coords = {
            'time': times,
            'latitude': lat_grid,
            'longitude': lon_grid
        }
        
        ds = xr.Dataset(data_vars, coords=coords)
        
        # Adicionar atributos
        ds.attrs['title'] = 'SWOT SSH Data - Cyclone Akará Region'
        ds.attrs['region'] = f'Lon: {lon_min:.2f} to {lon_max:.2f}, Lat: {lat_min:.2f} to {lat_max:.2f}'
        ds.attrs['resolution'] = f'{resolution} degrees'
        ds.attrs['created'] = pd.Timestamp.now().isoformat()
        
        return ds

def main():
    """Função principal."""
    print("🛰️ PROCESSAMENTO DOS DADOS SSH DO SWOT")
    print("=" * 50)
    
    # Criar processador
    processor = SWOTSSHProcessor()
    
    # Processar todos os arquivos
    processed_data = processor.process_all_files()
    
    if processed_data:
        # Criar dataset gridded
        gridded_ds = processor.create_gridded_dataset(processed_data)
        
        if gridded_ds is not None:
            # Salvar dataset gridded
            gridded_file = processor.processed_dir / "swot_ssh_gridded.nc"
            gridded_ds.to_netcdf(gridded_file)
            print(f"💾 Dataset gridded salvo em: {gridded_file}")
            
            print("\n📊 RESUMO DO DATASET GRIDDED:")
            print(f"🌍 Dimensões: {dict(gridded_ds.dims)}")
            print(f"📋 Variáveis: {list(gridded_ds.data_vars)}")
            if gridded_ds.time.size > 0:
                print(f"📅 Período: {gridded_ds.time.min().values} a {gridded_ds.time.max().values}")
            else:
                print(f"📅 Período: Sem dados de tempo válidos")
            
            print("\n✅ Processamento concluído com sucesso!")
            print("🚀 Próximo passo: executar scripts de visualização")
        else:
            print("❌ Falha ao criar dataset gridded")
    else:
        print("❌ Falha no processamento dos dados")

if __name__ == "__main__":
    main()