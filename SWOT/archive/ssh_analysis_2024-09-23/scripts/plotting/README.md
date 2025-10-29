# Scripts de Plotting/Visualização

Esta pasta contém scripts para criar visualizações profissionais dos dados SSH do SWOT.

## Scripts Disponíveis

### `create_ssh_maps.py`
Cria mapas estáticos de alta qualidade para conferências científicas.

**Características:**
- Mapas instantâneos de SSH, SWH e wind speed
- Mapas multi-variáveis em uma figura
- Série temporal de mapas
- Estilo profissional com Cartopy
- Coloração oceanográfica (cmocean)
- Formatos PNG e PDF

**Uso:**
```bash
python create_ssh_maps.py
```

### `create_ssh_animation.py`
Cria animações profissionais para apresentações.

**Características:**
- Animação temporal de SSH
- Animação multi-variável
- Estilo escuro para apresentações
- Formatos MP4 e GIF
- Configuração otimizada para Waves Workshop

**Uso:**
```bash
python create_ssh_animation.py
```

## Pipeline Completo

### `run_ssh_pipeline.py`
Executa todo o fluxo: processamento → mapas → animações

**Uso:**
```bash
python run_ssh_pipeline.py
```

Este script:
1. Verifica o ambiente
2. Processa dados brutos SSH
3. Cria mapas estáticos
4. Gera animações
5. Fornece relatório completo

## Pré-requisitos

### Dados
- Dados SWOT baixados em `data/raw/SWOT_L2_LR_SSH_Basic_2.0/`
- Execute primeiro os scripts de download

### Dependências
```bash
conda install -c conda-forge xarray matplotlib cartopy cmocean pandas numpy
```

### Para animações (opcional)
```bash
conda install -c conda-forge ffmpeg  # Para MP4
pip install pillow                   # Para GIF
```

## Saídas Geradas

### Mapas Estáticos
- `swot_ssh_snapshot.png/pdf` - Mapa instantâneo de SSH
- `swot_multi_variable.png/pdf` - Mapa multi-variável
- `swot_ssh_map_YYYYMMDD_HHMM.png/pdf` - Série temporal

### Animações
- `swot_ssh_animation.mp4/gif` - Animação de SSH
- `swot_multi_animation.mp4` - Animação multi-variável

## Configurações

### Estilo Científico (Mapas)
- Fundo branco/cinza claro
- Coastlines e borders bem definidos
- Grid com labels
- Coloração cmocean
- DPI 300 para publicação

### Estilo Apresentação (Animações)
- Fundo preto
- Coastlines douradas
- Texto branco em negrito
- Marca d'água "Waves Workshop"
- Otimizado para projeção

## Personalização

### Região
Modifique no script de processamento:
```python
region_bounds = {
    'lat_min': -45.0,
    'lat_max': -15.0,
    'lon_min': -50.0,
    'lon_max': -20.0
}
```

### Colormaps
- SSH: `cmocean.cm.balance` (anomalia)
- SWH: `cmocean.cm.amp` (amplitude)
- Wind: `cmocean.cm.speed` (velocidade)

### Animação
- FPS: 2 (padrão para apresentação)
- Duração: 8-10 segundos
- Formato: MP4 (alta qualidade) ou GIF (menor arquivo)

## Solução de Problemas

### Erro: "cartopy não encontrado"
```bash
conda install -c conda-forge cartopy
```

### Erro: "cmocean não encontrado"
```bash
conda install -c conda-forge cmocean
```

### Erro: "ffmpeg não encontrado" (animações MP4)
```bash
conda install -c conda-forge ffmpeg
```

### Dados não processados
Execute primeiro:
```bash
python ../processing/process_ssh_data.py
```

### Mapas vazios
- Verifique se há dados válidos na região
- Ajuste os limites regionais
- Verifique qualidade dos dados SWOT

## Dicas para Apresentação

### Waves Workshop
- Use animações MP4 (melhor qualidade)
- Fundo escuro funciona bem em projetores
- Duração 8-10s é ideal para explicação
- Inclua legendas e timestamps claros

### Mapas para Paper
- Use formatos PDF (vetorial)
- DPI 300 mínimo
- Coloração cmocean (padrão oceanográfico)
- Inclua informações do dataset

## Exemplos de Uso

### Mapa específico
```python
from create_ssh_maps import SWOTSSHMapper

mapper = SWOTSSHMapper()
fig, ax = mapper.plot_ssh_snapshot(time_idx=5, variable='ssh_karin')
mapper.save_figure(fig, 'meu_mapa_ssh')
```

### Animação customizada
```python
from create_ssh_animation import SWOTSSHAnimator

animator = SWOTSSHAnimator()
anim, fig = animator.create_ssh_animation(fps=3, duration_seconds=12)
animator.save_animation(anim, 'animacao_custom', format='mp4')
```