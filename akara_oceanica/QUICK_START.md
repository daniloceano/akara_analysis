# 🌊 Guia Rápido - Visualização de Trajetórias de Satélites

## 🚀 Início Rápido

### Opção 1: Teste Rápido (Recomendado para começar)
Baixa apenas Jason-3 e gera uma figura de teste:

```bash
cd scripts
python test_quick_plot.py
```

### Opção 2: Download Completo
Baixa todos os 10 satélites (pode demorar bastante):

```bash
cd scripts
python download_satellite_data.py
```

Depois, gere a figura:

```bash
python plot_satellite_tracks.py
```

### Opção 3: Download Individual
Escolha um satélite específico:

```bash
cd scripts
python download_single_satellite.py Jason-3
```

Satélites disponíveis:
- CFOSAT
- CryoSat-2
- HaiYang-2B
- HaiYang-2C
- Jason-3
- Saral/AltiKa (use: `python download_single_satellite.py "Saral/AltiKa"`)
- Sentinel-3A
- Sentinel-3B
- Sentinel-6A
- SWOT_nadir

## 📊 Scripts de Visualização

### 1. Básico - Trajetórias Simples
```bash
cd scripts
python plot_satellite_tracks.py
```
- Mapa limpo e claro
- Trajetórias coloridas por satélite
- Labels com datas
- Salva em: `figures/satellite_tracks_akara.png`

### 2. Avançado - Com Altura de Ondas
```bash
cd scripts
python plot_satellite_tracks_advanced.py
```
- Mapa estilo oceânico
- Colormap mostrando altura de ondas
- Trajetórias com linhas conectadas
- Labels detalhados (satélite + data + hora)
- Salva em: `figures/satellite_tracks_advanced.png`

### 3. Jupyter Notebook - Análise Interativa
```bash
jupyter notebook notebooks/satellite_tracks_analysis.ipynb
```
- Análise exploratória
- Estatísticas de altura de ondas
- Histogramas
- Plots interativos

## 🎨 Customização

### Modificar Região de Interesse
Edite `scripts/config.py`:

```python
BBOX = {
    'south': -45.0,   # Latitude sul
    'north': -15.0,   # Latitude norte  
    'west': -50.0,    # Longitude oeste
    'east': -20.0     # Longitude leste
}
```

### Modificar Período
Edite `scripts/config.py`:

```python
START_DATE = "2024-02-14"
END_DATE = "2024-02-22"
```

### Modificar Cores dos Satélites
Edite `plot_satellite_tracks.py` ou `plot_satellite_tracks_advanced.py`:

```python
SATELLITE_COLORS = {
    'Jason-3': '#00FF00',  # Verde
    # etc...
}
```

## 📂 Estrutura de Arquivos

Após executar os scripts, você terá:

```
akara_oceanica/
├── data/
│   ├── CFOSAT/
│   │   └── CFOSAT_Akara_2024-02-14_2024-02-22.nc
│   ├── Jason-3/
│   │   └── Jason-3_Akara_2024-02-14_2024-02-22.nc
│   └── ... (outros satélites)
├── figures/
│   ├── satellite_tracks_akara.png
│   └── satellite_tracks_advanced.png
└── scripts/
    └── ... (scripts)
```

## 🐛 Troubleshooting

### Erro de autenticação
As credenciais já estão configuradas em `config.py`. Se houver erro:
```bash
copernicusmarine login
```

### Nenhum dado disponível
Verifique se o download foi concluído com sucesso:
```bash
ls -lh data/*/
```

### Erro com cartopy
Instale dependências do sistema (macOS):
```bash
brew install proj geos
pip install cartopy
```

### Figura não aparece
Certifique-se de que há dados baixados:
```bash
python scripts/download_single_satellite.py Jason-3
python scripts/plot_satellite_tracks.py
```

## 💡 Dicas

1. **Começe com um satélite**: Use `test_quick_plot.py` ou baixe apenas Jason-3
2. **Download em background**: O download pode demorar. Use `nohup` ou `screen`
3. **Verifique cobertura**: Nem todos os satélites passam pela região todos os dias
4. **Alta resolução**: As figuras são salvas em 300 DPI, prontas para publicação
5. **Customização**: Todos os scripts são modulares e fáceis de modificar

## 📖 Mais Informações

- **Copernicus Marine**: https://marine.copernicus.eu/
- **Documentação copernicusmarine**: https://help.marine.copernicus.eu/
- **Cartopy docs**: https://scitools.org.uk/cartopy/

## 🆘 Ajuda

Se encontrar problemas:
1. Verifique os logs de erro
2. Confirme que as credenciais estão em `config.py`
3. Teste com um único satélite primeiro
4. Verifique a conexão com internet

---

**Bom trabalho! 🚀🌊**
