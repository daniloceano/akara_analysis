#!/usr/bin/env python3
"""
Processar dados SWOT WindWave - versão simplificada
"""

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import glob
import warnings
warnings.filterwarnings('ignore')

def process_swot_windwave():
    """
    Process SWOT WindWave data to extract SWH
    """
    
    print("🌊 PROCESSANDO DADOS SWOT WINDWAVE")
    print("="*60)
    
    # Paths
    data_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/raw/SWOT_L2_LR_SSH_WINDWAVE_2.0")
    output_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT/data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find WindWave files
    windwave_files = sorted(glob.glob(str(data_dir / "*.nc")))
    
    if not windwave_files:
        print("❌ Nenhum arquivo WindWave encontrado")
        return
        
    print(f"📁 Encontrados {len(windwave_files)} arquivos WindWave")
    
    # Collect all data for stats
    all_swh_data = []
    all_times = []
    all_lats = []
    all_lons = []
    file_info = []
    
    for i, file_path in enumerate(windwave_files):
        print(f"\\n📊 Processando {i+1}/{len(windwave_files)}: {Path(file_path).name}")
        
        try:
            ds = xr.open_dataset(file_path)
            
            # Extract SWH data
            swh_karin = ds.swh_karin.values
            times = ds.time.values
            lats = ds.latitude.values
            lons = ds.longitude.values
            
            # Flatten arrays
            swh_flat = swh_karin.flatten()
            times_flat = np.repeat(times, swh_karin.shape[1]) if len(times.shape) == 1 else times.flatten()
            lats_flat = lats.flatten()
            lons_flat = lons.flatten()
            
            # Remove NaN values
            valid_mask = ~(np.isnan(swh_flat) | np.isnan(lats_flat) | np.isnan(lons_flat))
            
            if valid_mask.any():
                swh_valid = swh_flat[valid_mask]
                times_valid = times_flat[valid_mask] if len(times_flat) == len(swh_flat) else times_flat[:len(swh_flat)][valid_mask]
                lats_valid = lats_flat[valid_mask]
                lons_valid = lons_flat[valid_mask]
                
                # Collect data
                all_swh_data.extend(swh_valid)
                all_times.extend(times_valid)
                all_lats.extend(lats_valid)
                all_lons.extend(lons_valid)
                
                # File statistics
                file_info.append({
                    'file': Path(file_path).name,
                    'valid_points': len(swh_valid),
                    'swh_min': swh_valid.min(),
                    'swh_max': swh_valid.max(),
                    'swh_mean': swh_valid.mean(),
                    'time_start': times_valid.min() if len(times_valid) > 0 else None,
                    'time_end': times_valid.max() if len(times_valid) > 0 else None
                })
                
                print(f"   SWH KaRIn: {swh_valid.min():.2f} - {swh_valid.max():.2f} m (média: {swh_valid.mean():.2f} m)")
                print(f"   Pontos válidos: {len(swh_valid):,}")
            else:
                print("   ⚠️ Nenhum dado válido encontrado")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            continue
    
    if not all_swh_data:
        print("❌ Nenhum dado válido foi processado")
        return
        
    print(f"\\n✅ Processamento concluído!")
    print(f"📊 Total de pontos válidos: {len(all_swh_data):,}")
    
    # Convert to numpy arrays
    swh_array = np.array(all_swh_data)
    times_array = np.array(all_times)
    lats_array = np.array(all_lats)  
    lons_array = np.array(all_lons)
    
    # Create simple dataset
    print("\\n💾 Criando dataset combinado...")
    
    # Create a simple combined dataset
    combined_data = {
        'swh_karin': (['obs'], swh_array),
        'latitude': (['obs'], lats_array),
        'longitude': (['obs'], lons_array),
        'time': (['obs'], times_array)
    }
    
    combined_ds = xr.Dataset(combined_data)
    
    # Add attributes
    combined_ds.swh_karin.attrs = {
        'long_name': 'Significant Wave Height from KaRIn',
        'units': 'm',
        'source': 'SWOT L2 LR SSH WindWave'
    }
    
    # Save combined dataset
    output_file = output_dir / "swot_windwave_swh_combined.nc"
    combined_ds.to_netcdf(output_file)
    print(f"✅ Dataset combinado salvo: {output_file}")
    
    # Create statistics
    print("\\n📊 ESTATÍSTICAS GERAIS")
    print("-" * 40)
    
    print(f"Total de arquivos processados: {len(file_info)}")
    print(f"Total de observações: {len(swh_array):,}")
    print()
    
    print(f"SWH Estatísticas:")
    print(f"  Mínimo: {swh_array.min():.3f} m")
    print(f"  Máximo: {swh_array.max():.3f} m")
    print(f"  Média: {swh_array.mean():.3f} m")
    print(f"  Mediana: {np.median(swh_array):.3f} m")
    print(f"  Desvio padrão: {swh_array.std():.3f} m")
    
    # Percentiles
    p25, p75, p95, p99 = np.percentile(swh_array, [25, 75, 95, 99])
    print(f"  P25: {p25:.3f} m")
    print(f"  P75: {p75:.3f} m")
    print(f"  P95: {p95:.3f} m") 
    print(f"  P99: {p99:.3f} m")
    
    # Temporal coverage
    times_pd = pd.to_datetime(times_array)
    print(f"\\nCobertura Temporal:")
    print(f"  Início: {times_pd.min().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Fim: {times_pd.max().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duração: {(times_pd.max() - times_pd.min()).total_seconds() / 3600:.1f} horas")
    
    # Spatial coverage
    print(f"\\nCobertura Espacial:")
    print(f"  Latitude: {lats_array.min():.3f}° a {lats_array.max():.3f}°")
    print(f"  Longitude: {lons_array.min():.3f}° a {lons_array.max():.3f}°")
    
    # Save file statistics
    stats_file = output_dir / "swot_windwave_file_stats.csv"
    file_df = pd.DataFrame(file_info)
    file_df.to_csv(stats_file, index=False)
    print(f"\\n📄 Estatísticas por arquivo salvas: {stats_file}")
    
    # Save overall statistics
    overall_stats = {
        'processing_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_files': len(file_info),
        'total_observations': len(swh_array),
        'swh_min': float(swh_array.min()),
        'swh_max': float(swh_array.max()),
        'swh_mean': float(swh_array.mean()),
        'swh_median': float(np.median(swh_array)),
        'swh_std': float(swh_array.std()),
        'swh_p25': float(p25),
        'swh_p75': float(p75),
        'swh_p95': float(p95),
        'swh_p99': float(p99),
        'time_start': str(times_pd.min()),
        'time_end': str(times_pd.max()),
        'duration_hours': float((times_pd.max() - times_pd.min()).total_seconds() / 3600),
        'lat_min': float(lats_array.min()),
        'lat_max': float(lats_array.max()),
        'lon_min': float(lons_array.min()),
        'lon_max': float(lons_array.max())
    }
    
    stats_summary_file = output_dir / "swot_windwave_summary_stats.json"
    import json
    with open(stats_summary_file, 'w') as f:
        json.dump(overall_stats, f, indent=2)
    
    print(f"📊 Resumo estatístico salvo: {stats_summary_file}")
    
    return combined_ds

if __name__ == "__main__":
    result = process_swot_windwave()
    
    if result is not None:
        print("\\n🎯 PRÓXIMOS PASSOS:")
        print("1. Criar grid regular dos dados SWH SWOT")
        print("2. Combinar com dados ERA5 SWH") 
        print("3. Criar visualizações comparativas SWH SWOT vs ERA5")
        print("4. Análise de correlação e validação")
    else:
        print("\\n❌ Processamento falhou")