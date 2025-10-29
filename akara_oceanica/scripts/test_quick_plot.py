"""
Script de exemplo para testar download e plotagem rápida
Baixa apenas Jason-3 (mais rápido) e gera a figura de trajetórias
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretório base do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check_data_exists(satellite_name='Jason-3'):
    """
    Verifica se os dados do satélite já foram baixados
    """
    data_dir = PROJECT_ROOT / 'data' / satellite_name.replace('/', '_')
    
    if not data_dir.exists():
        return False
    
    csv_files = list(data_dir.glob('*.csv'))
    return len(csv_files) > 0


def main():
    logger.info("=" * 60)
    logger.info("🚀 TESTE RÁPIDO - DOWNLOAD E PLOTAGEM 🌊")
    logger.info("=" * 60)
    logger.info("")
    
    satellite = "Jason-3"
    
    # Verificar se dados já existem
    if check_data_exists(satellite):
        logger.info(f"✅ Dados do {satellite} já existem! Pulando download...")
        logger.info("")
    else:
        # Passo 1: Download de um satélite (Jason-3 é geralmente rápido)
        logger.info("📡 Passo 1/2: Baixando dados do Jason-3...")
        logger.info("")
        
        try:
            result = subprocess.run(
                [sys.executable, "download_single_satellite.py", satellite],
                cwd=PROJECT_ROOT / "scripts",
                check=True,
                capture_output=False
            )
            logger.info("")
            logger.info("✅ Download concluído!")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro no download: {e}")
            logger.info("\n💡 Você pode tentar baixar manualmente:")
            logger.info(f"   cd scripts && python download_single_satellite.py {satellite}")
            return
    
    # Passo 2: Plotar trajetórias
    logger.info("")
    logger.info("🗺️  Passo 2/2: Gerando figura de trajetórias...")
    logger.info("")
    
    try:
        result = subprocess.run(
            [sys.executable, "plot_satellite_tracks.py"],
            cwd=PROJECT_ROOT / "scripts",
            check=True,
            capture_output=False
        )
        logger.info("")
        logger.info("✅ Figura gerada!")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro na plotagem: {e}")
        logger.info("\n💡 Você pode tentar plotar manualmente:")
        logger.info("   cd scripts && python plot_satellite_tracks.py")
        return
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 TESTE CONCLUÍDO COM SUCESSO! 🎊")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📁 Figura salva em: figures/satellite_tracks_akara.png")
    logger.info("")
    logger.info("💡 Próximos passos:")
    logger.info("   1. Para baixar TODOS os satélites:")
    logger.info("      cd scripts && python download_satellite_data.py")
    logger.info("   2. Depois gere a figura completa:")
    logger.info("      cd scripts && python plot_satellite_tracks.py")
    logger.info("   3. Ou a versão avançada (com altura de ondas):")
    logger.info("      cd scripts && python plot_satellite_tracks_advanced.py")


if __name__ == "__main__":
    main()
