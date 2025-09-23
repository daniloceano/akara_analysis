# Scripts de Download

Esta pasta contém scripts para baixar dados SWOT do período do ciclone Akará (14-22 de fevereiro de 2024).

## Arquivos

### `download_swot_data.py`
Script principal para download dos dados SWOT usando o podaac-data-subscriber.

**Características:**
- Período: 14 a 22 de fevereiro de 2024
- Região: Atlântico Sul (aproximada para o ciclone Akará)
- Datasets: SWOT Level 2 SSH Basic e River Single Pass
- Verificação automática de dependências e credenciais

### `setup_credentials.py`
Script auxiliar para configurar credenciais NASA Earthdata.

**Funcionalidades:**
- Criação do arquivo .netrc
- Teste de credenciais
- Instalação automática do podaac-data-subscriber

### `run_download.py`
Script exemplo que executa todo o fluxo: configuração → download → verificação.

## Como usar

### Primeira vez (configuração completa)
```bash
# 1. Instalar dependências (se ainda não instalado)
conda install -c conda-forge podaac-data-subscriber xarray netcdf4 h5py matplotlib cartopy

# 2. Executar fluxo completo
python run_download.py
```

### Configuração manual
```bash
# 1. Configurar credenciais
python setup_credentials.py

# 2. Baixar dados
python download_swot_data.py
```

### Apenas download (se já configurado)
```bash
python download_swot_data.py
```

## Pré-requisitos

1. **Conta NASA Earthdata**
   - Criar em: https://urs.earthdata.nasa.gov/
   - Necessária para acessar dados SWOT

2. **Dependências Python**
   - `podaac-data-subscriber>=1.14.0`
   - Outras listadas em `requirements.txt`

3. **Conexão estável com internet**
   - Downloads podem ser grandes (vários GB)

## Configuração da região

A região padrão está configurada para o Atlântico Sul:
- Sul: -45°S
- Norte: -15°S  
- Oeste: -50°W
- Leste: -20°W

Para modificar, edite as variáveis `BBOX` em `download_swot_data.py`.

## Datasets baixados

1. **SWOT_L2_LR_SSH_Basic_2.0**
   - Altura da superfície do mar
   - Backscatter sigma0
   - Velocidade do vento

2. **SWOT_L2_HR_RiverSP_2.0**
   - Elevação da superfície da água
   - Largura dos rios
   - Inclinação

## Solução de problemas

### Erro de credenciais
- Verificar username/senha NASA Earthdata
- Reexecutar `setup_credentials.py`
- Verificar arquivo `~/.netrc`

### Erro de conexão
- Verificar conexão com internet
- Tentar novamente após alguns minutos
- Servidores NASA podem estar temporariamente indisponíveis

### Dados não encontrados
- Verificar se dados estão disponíveis para o período
- SWOT pode não ter passado sobre a região exata nas datas
- Considerar expandir a região ou período de busca