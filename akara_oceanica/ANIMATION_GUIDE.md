# 🎬 Guia de Animações - ERA5 + Satélites

## 📋 Visão Geral

Este guia explica como criar animações profissionais combinando:
- **Campos ERA5** (background): Dados de reanálise em grade regular, horários
- **Dados de Satélites** (overlay): Dados altimétricos ao longo das trajetórias, por minuto

## 🚀 Fluxo de Trabalho

### 1️⃣ Pré-requisitos

Instalar dependências adicionais:
```bash
conda activate akara
pip install cmocean ffmpeg-python
```

No macOS, instalar ffmpeg:
```bash
brew install ffmpeg
```

### 2️⃣ Baixar Dados ERA5

```bash
cd scripts
python download_era5_waves.py
```

**O que faz:**
- Conecta ao Copernicus Climate Data Store (CDS)
- Baixa dados ERA5 de ondas para 16-20 fev 2024
- Salva em `data/era5_waves/era5_waves_akara_*.nc`
- Variáveis: altura de onda, direção, período

**Nota:** Requer credenciais CDS configuradas em `~/.cdsapirc`

### 3️⃣ Testar Preview (Opcional mas Recomendado)

```bash
python test_animation_preview.py
```

**O que faz:**
- Cria 5 frames PNG de exemplo
- Mostra ERA5 + Jason-3
- Salva em `figures/animation_preview/`
- Útil para verificar antes de criar vídeos

### 4️⃣ Criar Animações Completas

```bash
python create_wave_animations.py
```

**O que faz:**
- Carrega todos os dados (ERA5 + 10 satélites)
- Cria bins temporais horários
- Para cada hora ERA5, busca dados de satélite ±30 min
- Gera animações MP4:
  - 1 com todos os satélites
  - 10 individuais (uma por satélite)

**Tempo estimado:** 
- Preview: ~1 minuto
- Animação completa: ~10-30 minutos (depende do número de frames)

## 📊 Detalhes Técnicos

### Sincronização Temporal

- **ERA5**: Dados horários (00:00, 01:00, 02:00, ...)
- **Satélites**: Medições por segundo/minuto
- **Solução**: Para cada hora ERA5, incluir dados de satélite na janela [-30min, +30min]

Exemplo:
```
ERA5: 2024-02-16 12:00
Satélites: dados entre 11:30 e 12:30
```

### Resolução Espacial

- **ERA5**: Grade regular 0.25° (~28 km)
- **Satélites**: Pontos ao longo da trajetória

### Visualização

**Camadas (de baixo para cima):**
1. Campo ERA5 (contourf, alpha=0.8)
2. Continentes e costas
3. Pontos de satélite (scatter, coloridos)

**Cores:**
- Todos juntos: Cada satélite tem cor própria
- Individual: Pontos coloridos por altura de onda

## 🎨 Customização

### Ajustar FPS e Qualidade

Editar `create_wave_animations.py`:

```python
# Linha ~420
animator.create_animation(satellite=None, fps=2, interval=500)
#                                          ^      ^
#                                          |      Intervalo (ms)
#                                          Frames/segundo
```

**Sugestões:**
- Apresentação: `fps=2, interval=500`
- Análise rápida: `fps=5, interval=200`
- Alta qualidade: `fps=1, interval=1000`

### Mudar Região

Editar `create_wave_animations.py`:

```python
# Linha ~66
region = {
    'west': -50.0,
    'east': -20.0,
    'south': -45.0,
    'north': -15.0
}
```

### Mudar Escala de Cores

```python
# Linha ~281 (ERA5 background)
vmin=0,
vmax=8,  # Altura máxima em metros

# Linha ~300 (satélites)
vmin=0,
vmax=8,
```

### Mudar Colormap

```python
# Usar cmocean (oceânico)
cmap=cmocean.cm.amp   # Ondas (default)
cmap=cmocean.cm.thermal  # Térmico
cmap=cmocean.cm.haline   # Salinidade

# Usar matplotlib
cmap='viridis'
cmap='plasma'
cmap='jet'
```

## 📁 Estrutura de Saída

```
figures/
├── animation_preview/        # Frames de teste (PNG)
│   ├── preview_frame_000.png
│   ├── preview_frame_001.png
│   └── ...
└── animations/               # Vídeos finais (MP4)
    ├── wave_animation_all_satellites.mp4
    ├── wave_animation_Jason-3.mp4
    ├── wave_animation_Sentinel-3A.mp4
    └── ...
```

## 🐛 Troubleshooting

### Erro: "ERA5 não encontrado"
```bash
python scripts/download_era5_waves.py
```

### Erro: "No module named 'cmocean'"
```bash
pip install cmocean
```

### Erro: "ffmpeg not found"
**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Animação muito lenta
1. Reduzir número de frames (editar período no ERA5)
2. Aumentar FPS (menos frames por segundo = mais rápido)
3. Reduzir resolução espacial

### Sem dados de satélite aparecendo
- Verificar se satélites têm dados no período ERA5
- Ajustar janela temporal (±30 min → ±60 min)
- Verificar logs para warnings

## 💡 Dicas

1. **Sempre teste com preview primeiro**
   ```bash
   python test_animation_preview.py
   ```

2. **Crie animações individuais antes da combinada**
   - Mais rápido de processar
   - Mais fácil de debugar
   - Permite comparação

3. **Use screen/tmux para processos longos**
   ```bash
   screen -S animations
   python create_wave_animations.py
   # Ctrl+A, D para detach
   ```

4. **Combine vídeos com ffmpeg (opcional)**
   ```bash
   # Criar montagem 2x2
   ffmpeg -i wave_animation_Jason-3.mp4 \
          -i wave_animation_Sentinel-3A.mp4 \
          -i wave_animation_CryoSat-2.mp4 \
          -i wave_animation_CFOSAT.mp4 \
          -filter_complex "[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]" \
          -map "[v]" montage_4sat.mp4
   ```

## 🎯 Exemplos de Uso

### Caso 1: Análise Rápida
```bash
# Só preview
python test_animation_preview.py
open figures/animation_preview/
```

### Caso 2: Um Satélite Específico
Editar `create_wave_animations.py`, comentar o loop e manter:
```python
animator.create_animation(satellite='Jason-3', fps=3, interval=300)
```

### Caso 3: Produção Completa
```bash
# Baixar tudo
python download_era5_waves.py
python download_satellite_data.py

# Preview
python test_animation_preview.py

# Criar todas animações
python create_wave_animations.py

# Resultado: 11 vídeos MP4
```

## 📖 Referências

- **ERA5**: https://cds.climate.copernicus.eu/
- **CMEMS**: https://marine.copernicus.eu/
- **cmocean**: https://matplotlib.org/cmocean/
- **FFmpeg**: https://ffmpeg.org/

---

**Boa animação! 🎬🌊🛰️**
