"""
Script para baixar dados de satélites L3 do CMEMS para análise oceânica do ciclone Akará
"""

import os
from pathlib import Path
import copernicusmarine
from datetime import datetime
import logging
from config import START_DATE, END_DATE, BBOX, DATASETS, VARIABLES, DEPTH, COPERNICUS_USERNAME, COPERNICUS_PASSWORD

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretório base do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_data_directories(base_dir='data'):
    """
    Cria diretórios para armazenar dados de cada satélite
    """
    base_path = PROJECT_ROOT / base_dir
    base_path.mkdir(exist_ok=True)
    
    for satellite in DATASETS.keys():
        satellite_dir = base_path / satellite.replace('/', '_')
        satellite_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Diretório criado: {satellite_dir}")
    
    return base_path


def download_dataset(satellite_name, dataset_id, output_dir):
    """
    Baixa dados de um satélite específico
    
    Parameters
    ----------
    satellite_name : str
        Nome do satélite
    dataset_id : str
        ID do dataset no CMEMS
    output_dir : Path
        Diretório de saída
    """
    logger.info(f"🛰️  Iniciando download de {satellite_name}...")
    
    # Nome do arquivo de saída
    output_filename = f"{satellite_name.replace('/', '_')}_Akara_{START_DATE}_{END_DATE}.nc"
    output_path = output_dir / output_filename
    
    try:
        copernicusmarine.subset(
            dataset_id=dataset_id,
            variables=VARIABLES,
            minimum_longitude=BBOX['west'],
            maximum_longitude=BBOX['east'],
            minimum_latitude=BBOX['south'],
            maximum_latitude=BBOX['north'],
            start_datetime=f"{START_DATE}T00:00:00",
            end_datetime=f"{END_DATE}T23:59:59",
            minimum_depth=DEPTH['minimum'],
            maximum_depth=DEPTH['maximum'],
            output_filename=str(output_path),
            force_download=True,
            username=COPERNICUS_USERNAME,
            password=COPERNICUS_PASSWORD
        )
        logger.info(f"✅ Download concluído: {output_filename} 🎉")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao baixar {satellite_name}: {str(e)} 😢")
        return False


def download_all_datasets(base_dir='data'):
    """
    Baixa dados de todos os satélites configurados
    """
    base_path = create_data_directories(base_dir)
    
    logger.info(f"📅 Período: {START_DATE} a {END_DATE}")
    logger.info(f"🌍 Região: S={BBOX['south']}, N={BBOX['north']}, "
                f"W={BBOX['west']}, E={BBOX['east']}")
    logger.info(f"🛰️  Total de satélites: {len(DATASETS)}\n")
    
    results = {}
    
    for satellite_name, dataset_id in DATASETS.items():
        satellite_dir = base_path / satellite_name.replace('/', '_')
        success = download_dataset(satellite_name, dataset_id, satellite_dir)
        results[satellite_name] = success
        logger.info("")  # Linha em branco entre downloads
    
    # Sumário
    logger.info("=" * 60)
    logger.info("📊 SUMÁRIO DO DOWNLOAD")
    logger.info("=" * 60)
    
    successful = sum(results.values())
    failed = len(results) - successful
    
    logger.info(f"✅ Sucessos: {successful}/{len(results)}")
    logger.info(f"❌ Falhas: {failed}/{len(results)}")
    
    if failed > 0:
        logger.info("\n⚠️  Satélites com falha:")
        for satellite, success in results.items():
            if not success:
                logger.info(f"  🔴 {satellite}")
    
    return results
    
    return results


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🌊 DOWNLOAD DE DADOS SATELITAIS - CICLONE AKARÁ 🌀")
    logger.info("=" * 60)
    logger.info("")
    
    results = download_all_datasets()
    
    logger.info("")
    logger.info("🎊 Download finalizado! 🚀")
