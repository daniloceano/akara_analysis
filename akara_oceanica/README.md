# Análise Oceânica - Ciclone Akará

Análise oceanográfica do ciclone Akará (14-22 de fevereiro de 2024) utilizando dados de satélites L3 do Copernicus Marine Service.

## Estrutura do Projeto

```
akara_oceanica/
├── data/           # Dados baixados de satélites (por satélite)
figures/
├── animation_preview/
│   ├── preview_frame_000.png  ← ERA5 + Jason-3
│   ├── preview_frame_001.png
│   └── ...
└── animations/
    ├── wave_animation_all_satellites.mp4  ← TODOS
    ├── wave_animation_Jason-3.mp4         ← Individual
    ├── wave_animation_Sentinel-3A.mp4
    ├── wave_animation_CryoSat-2.mp4
    └── ... (10 satélites)│   ├── era5_waves/ # Dados ERA5 (campos de ondas)
│   ├── CFOSAT/
│   ├── Jason-3/
│   └── ...
├── figures/        # Figuras e gráficos
│   ├── animations/ # Animações MP4
│   └── ...
├── notebooks/      # Jupyter notebooks para análise
├── scripts/        # Scripts Python
│   ├── config.py                          # Configurações gerais
│   ├── download_satellite_data.py         # Download de todos os satélites
│   ├── download_single_satellite.py       # Download de satélite individual
│   ├── download_era5_waves.py             # Download dados ERA5
│   ├── plot_satellite_tracks.py           # Plotar trajetórias (básico)
│   ├── plot_satellite_tracks_advanced.py  # Plotar trajetórias (avançado)
│   ├── create_wave_animations.py          # Criar animações ERA5+satélites
│   ├── test_animation_preview.py          # Testar frames antes de animar
│   └── test_quick_plot.py                 # Teste rápido download + plot
└── README.md       # Este arquivo
```

## Período e Região

- **Período:** 14 a 22 de fevereiro de 2024
- **Região:** Atlântico Sul
  - Latitude: 45°S - 15°S
  - Longitude: 50°W - 20°W

## Satélites Utilizados

Dados L3 de ondas (wave height) de 10 satélites:
- CFOSAT
- CryoSat-2
- HaiYang-2B
- HaiYang-2C
- Jason-3
- Saral/AltiKa
- Sentinel-3A
- Sentinel-3B
- Sentinel-6A
- SWOT nadir

## Variáveis Baixadas

- `VAVH`: Altura significativa de onda
- `VAVH_UNFILTERED`: Altura significativa de onda (sem filtro)
- `WIND_SPEED`: Velocidade do vento

## Como Usar

### Instalação

Instalar dependências:
```bash
pip install -r requirements.txt
```

Ou instalar individualmente:
```bash
pip install copernicusmarine numpy pandas xarray netCDF4 matplotlib cartopy
```

### Download de Dados

**Baixar todos os satélites:**
```bash
cd scripts
python download_satellite_data.py
```

**Baixar satélite específico:**
```bash
cd scripts
python download_single_satellite.py Jason-3
```

Para ver satélites disponíveis:
```bash
python download_single_satellite.py --help
```

### Visualização de Trajetórias 🛰️

**Teste rápido (baixa 1 satélite + gera figura):**
```bash
cd scripts
python test_quick_plot.py
```

**Plotar trajetórias básicas:**
```bash
cd scripts
python plot_satellite_tracks.py
```

**Plotar trajetórias avançadas (com altura de ondas):**
```bash
cd scripts
python plot_satellite_tracks_advanced.py
```

As figuras são salvas em `figures/`:
- `satellite_tracks_akara.png` - Versão básica
- `satellite_tracks_advanced.png` - Versão com colormap de altura de ondas

### Animações 🎬

**1. Baixar dados ERA5 (necessário para animações):**
```bash
cd scripts
python download_era5_waves.py
```

**2. Testar frames individuais (antes de criar animação):**
```bash
python test_animation_preview.py
```
Cria 5 frames PNG de exemplo em `figures/animation_preview/`

**3. Criar animações completas:**
```bash
python create_wave_animations.py
```

Gera animações MP4 em `figures/animations/`:
- `wave_animation_all_satellites.mp4` - Todos os satélites juntos
- `wave_animation_Jason-3.mp4` - Jason-3 individual
- `wave_animation_Sentinel-3A.mp4` - Sentinel-3A individual
- ... (uma para cada satélite)

**Características das animações:**
- 🌊 Campos ERA5 de fundo (dados horários em grade)
- 🛰️ Dados de satélites sobrepostos (por minuto)
- ⏰ Janela temporal: ±30 minutos em torno de cada hora ERA5
- 🎨 Colormap oceanográfico (cmocean)
- 📊 Escala: 0-8 metros
- 🎞️ 2 FPS (ajustável)

## Configuração

Edite `scripts/config.py` para modificar:
- Período de análise
- Região de interesse (bounding box)
- Satélites a serem utilizados
- Variáveis a serem baixadas

## Credenciais CMEMS

O download requer credenciais do Copernicus Marine Service. 

**Configuração automática (recomendado):**
As credenciais já estão configuradas no `scripts/config.py`. O download não pedirá senha.

**Configuração manual alternativa:**
```bash
copernicusmarine login
```

**⚠️ Segurança:**
O arquivo `scripts/config.py` contém suas credenciais e está no `.gitignore` para não ser commitado no Git.
Se for compartilhar o projeto, use `scripts/config.py.template` como base.

## Notas

- Os dados L3 são dados ao longo da trajetória do satélite (track data)
- Nem todos os satélites passam sobre a região de interesse todos os dias
- O tamanho dos arquivos varia conforme a cobertura de cada satélite
