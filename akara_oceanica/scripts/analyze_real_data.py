import pandas as pd
import numpy as np
from pathlib import Path

satellites = {
    'CFOSAT': 'data/CFOSAT/CFOSAT_Akara_2024-02-14_2024-02-22.nc.csv',
    'CryoSat-2': 'data/CryoSat-2/CryoSat-2_Akara_2024-02-14_2024-02-22.nc.csv',
    'HaiYang-2B': 'data/HaiYang-2B/HaiYang-2B_Akara_2024-02-14_2024-02-22.nc.csv',
    'HaiYang-2C': 'data/HaiYang-2C/HaiYang-2C_Akara_2024-02-14_2024-02-22.nc.csv',
    'Jason-3': 'data/Jason-3/Jason-3_Akara_2024-02-14_2024-02-22.nc.csv',
    'Saral/AltiKa': 'data/Saral_AltiKa/Saral_AltiKa_Akara_2024-02-14_2024-02-22.nc.csv',
    'Sentinel-3A': 'data/Sentinel-3A/Sentinel-3A_Akara_2024-02-14_2024-02-22.nc.csv',
    'Sentinel-3B': 'data/Sentinel-3B/Sentinel-3B_Akara_2024-02-14_2024-02-22.nc.csv',
    'Sentinel-6A': 'data/Sentinel-6A/Sentinel-6A_Akara_2024-02-14_2024-02-22.nc.csv',
    'SWOT': 'data/SWOT_nadir/SWOT_nadir_Akara_2024-02-14_2024-02-22.nc.csv',
}

print('🌊 COMPARAÇÃO DE ALTURA DE ONDAS - TODOS OS SATÉLITES')
print('=' * 80)
print(f"{'Satélite':<15} {'Medições':<10} {'Mín (m)':<10} {'Máx (m)':<10} {'Média (m)':<10}")
print('-' * 80)

max_waves = []

for sat, file in satellites.items():
    if Path(file).exists():
        df = pd.read_csv(file)
        vavh = df[df['variable'] == 'VAVH']['value']
        
        print(f'{sat:<15} {len(vavh):<10,} {vavh.min():<10.2f} {vavh.max():<10.2f} {vavh.mean():<10.2f}')
        max_waves.append((sat, vavh.max()))

print('=' * 80)
print()
print('🏆 ONDAS MAIS ALTAS REGISTRADAS:')
max_waves.sort(key=lambda x: x[1], reverse=True)
for i, (sat, wave) in enumerate(max_waves[:5], 1):
    print(f'   {i}. {sat}: {wave:.2f} m')

print()
print('📍 FONTE: Copernicus Marine Service (CMEMS)')
print('🌐 Dados altimétricos de satélites L3 (along-track)')
print('📅 Período: 14-22 Fevereiro 2024 (Ciclone Akará)')
print('🌊 Região: Atlântico Sul (45°S-15°S, 50°W-20°W)')
