# Análise SWOT + WAVERYS - Ciclone Akará

Este projeto visa analisar dados do satélite SWOT (Surface Water and Ocean Topography) combinados com dados de reanálise WAVERYS para estudar as características oceanográficas durante a passagem do ciclone tropical Akará, que ocorreu em fevereiro de 2024 no Atlântico Sul.

## Objetivo

O objetivo principal é baixar, processar e visualizar dados observacionais (SWOT) e de modelo (WAVERYS) para compreender melhor os impactos do ciclone Akará nas condições oceanográficas da região, criando visualizações combinadas que mostrem:

- Altura da superfície do mar (SSH) do SWOT
- Altura significativa de ondas (SWH) do WAVERYS  
- Comparações temporais e espaciais entre observações e modelo
- Série temporal para ponto próximo ao Rio de Janeiro

## Estrutura do Projeto

```
SWOT/
├── README.md                 # Este arquivo
├── requirements.txt          # Dependências Python
├── data/                     # Dados do projeto
│   ├── raw/                 # Dados brutos baixados do SWOT
│   ├── processed/           # Dados SWOT processados e gridados
│   └── waverys/             # Dados WAVERYS baixados
├── scripts/                 # Scripts Python
│   ├── download/           # Scripts para download de dados SWOT
│   ├── processing/         # Scripts para processamento de dados SWOT
│   ├── plotting/           # Scripts para visualizações SWOT
│   ├── waverys/            # Scripts para download WAVERYS
│   └── visualization/      # Scripts para visualizações combinadas
├── figures/                # Figuras e mapas gerados
│   ├── ssh_maps/           # Mapas de SSH do SWOT
│   ├── animations/         # Animações
│   └── combined/           # Visualizações combinadas SWOT+WAVERYS
├── notebooks/              # Jupyter notebooks para análise exploratória
└── docs/                   # Documentação adicional
```

## Sobre o Ciclone Akará

O ciclone tropical Akará foi um evento meteorológico significativo que ocorreu em fevereiro de 2024 no Atlântico Sul, proporcionando uma oportunidade única para estudar as interações oceano-atmosfera utilizando dados de alta resolução do SWOT combinados com reanálise de ondas WAVERYS.

**Período de análise:** 14-22 de fevereiro de 2024

## Dados Utilizados

### SWOT (Surface Water and Ocean Topography)
- **Fonte:** NASA/CNES
- **Produto:** Level 2 SSH Basic
- **Resolução:** ~2 km cross-track
- **Variáveis:** SSH, qualidade, incerteza
- **Download:** podaac-data-subscriber

### WAVERYS (Global Ocean Waves Reanalysis)
- **Fonte:** Copernicus Marine Service
- **Dataset ID:** cmems_mod_glo_wav_my_0.2deg_PT3H-i
- **Resolução:** 0.2° (~22 km), 3 horas
- **Variáveis:** VHM0, VMDR, VTPK, VTM02, etc.
- **Download:** copernicusmarine

## Instalação e Uso

### 1. Criar ambiente conda
```bash
conda create -n swot python=3.11
conda activate swot
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciais
- **SWOT:** Registrar em https://urs.earthdata.nasa.gov/
- **WAVERYS:** Registrar em https://marine.copernicus.eu/

### 4. Executar pipeline

#### Download de dados:
```bash
# SWOT
python scripts/download/run_download.py

# WAVERYS 
python scripts/waverys/download_waverys_data.py
```

#### Processamento:
```bash
python scripts/processing/process_ssh_data.py
```

#### Visualizações:
```bash
# Mapas e animações SWOT
python scripts/plotting/create_ssh_maps.py
python scripts/plotting/create_ssh_animation.py

# Visualizações combinadas SWOT + WAVERYS
python scripts/visualization/create_combined_visualizations.py
```

## Principais Funcionalidades

### ✅ Implementado
- Download automático de dados SWOT
- Processamento e gridding de dados SSH
- Mapas instantâneos de SSH
- Animação temporal
- Download de dados WAVERYS (real ou sintético)
- Visualizações combinadas SWOT + WAVERYS
- Série temporal para Rio de Janeiro
- Correção de timestamps

### 🔄 Em desenvolvimento
- Análises estatísticas avançadas
- Validação SWOT vs WAVERYS
- Análise espectral de ondas

## Status do Projeto

✅ **Pipeline completo funcionando!** 
- Dados SWOT processados (26 arquivos, período 14-22 Feb 2024)
- Timestamps corrigidos 
- Visualizações profissionais criadas
- Integração WAVERYS implementada