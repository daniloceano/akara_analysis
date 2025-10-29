"""
Script para baixar dados de um satélite específico
Útil para testes ou downloads individuais
"""

import argparse
import logging
from pathlib import Path
from download_satellite_data import download_dataset, create_data_directories
from config import DATASETS, START_DATE, END_DATE, BBOX

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='🛰️  Baixar dados de um satélite específico para o período do Akará 🌊'
    )
    parser.add_argument(
        'satellite',
        type=str,
        choices=list(DATASETS.keys()),
        help='Nome do satélite para download'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='../data',
        help='Diretório base para salvar os dados (padrão: ../data)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info(f"🛰️  DOWNLOAD - {args.satellite} 🌀")
    logger.info("=" * 60)
    logger.info(f"📅 Período: {START_DATE} a {END_DATE}")
    logger.info(f"🌍 Região: S={BBOX['south']}, N={BBOX['north']}, "
                f"W={BBOX['west']}, E={BBOX['east']}")
    logger.info("")
    
    # Criar diretórios
    base_path = create_data_directories(args.output_dir)
    satellite_dir = base_path / args.satellite.replace('/', '_')
    
    # Download
    dataset_id = DATASETS[args.satellite]
    success = download_dataset(args.satellite, dataset_id, satellite_dir)
    
    if success:
        logger.info("\n✅ Download concluído com sucesso! 🎉")
    else:
        logger.error("\n❌ Download falhou. Verifique os logs acima. 😢")
        exit(1)


if __name__ == "__main__":
    main()
