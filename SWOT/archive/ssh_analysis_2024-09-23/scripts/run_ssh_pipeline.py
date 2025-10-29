#!/usr/bin/env python3
"""
Script principal para executar todo o pipeline de processamento e visualização SSH
Executa: processamento → mapas → animações

Autor: Danilo Couto de Souza
Data: Setembro 2025
Projeto: Análise SWOT - Ciclone Akará
"""

import subprocess
import sys
from pathlib import Path
import time

def run_script(script_path, description):
    """
    Executa um script Python e mostra o resultado.
    
    Parameters:
    -----------
    script_path : Path
        Caminho para o script
    description : str
        Descrição do que o script faz
    """
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📄 Executando: {script_path.name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print("✅ SUCESSO!")
            print(f"⏱️ Tempo: {elapsed_time:.1f}s")
            
            # Mostrar últimas linhas da saída
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                print("\n📋 Últimas mensagens:")
                for line in lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
            
            return True
            
        else:
            print("❌ ERRO!")
            print(f"💥 Código de erro: {result.returncode}")
            
            if result.stderr:
                print("\n🚨 Erro:")
                print(result.stderr[-500:])  # Últimos 500 caracteres do erro
            
            if result.stdout:
                print("\n📋 Saída:")
                print(result.stdout[-500:])
            
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT! Script demorou mais que 10 minutos.")
        return False
        
    except Exception as e:
        print(f"💥 ERRO INESPERADO: {e}")
        return False

def check_environment():
    """Verifica se o ambiente está configurado."""
    print("🔍 VERIFICANDO AMBIENTE")
    print("=" * 30)
    
    # Verificar diretórios
    base_dir = Path(__file__).parent.parent  # Vai para o diretório SWOT
    data_raw_dir = base_dir / "data" / "raw" / "SWOT_L2_LR_SSH_Basic_2.0"
    
    if not data_raw_dir.exists():
        print("❌ Dados brutos não encontrados!")
        print(f"📁 Esperado em: {data_raw_dir}")
        print("💡 Execute primeiro os scripts de download!")
        return False
    
    # Contar arquivos
    nc_files = list(data_raw_dir.glob("*.nc"))
    print(f"✅ Encontrados {len(nc_files)} arquivos NetCDF")
    
    if len(nc_files) == 0:
        print("❌ Nenhum arquivo NetCDF encontrado!")
        return False
    
    # Verificar dependências
    required_modules = ['xarray', 'matplotlib', 'cartopy', 'cmocean', 'pandas', 'numpy']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"\n🚨 Módulos faltando: {', '.join(missing_modules)}")
        print("💡 Instale com: conda install -c conda-forge " + " ".join(missing_modules))
        return False
    
    print("✅ Ambiente OK!")
    return True

def main():
    """Função principal."""
    print("🛰️ PIPELINE COMPLETO DE PROCESSAMENTO SSH SWOT")
    print("=" * 55)
    print("🎯 Ciclone Akará - Waves Workshop")
    print("👨‍💻 Danilo Couto de Souza")
    print()
    
    # Verificar ambiente
    if not check_environment():
        print("\n❌ Ambiente não está configurado corretamente!")
        print("🔧 Configure o ambiente e tente novamente.")
        return
    
    # Caminhos dos scripts
    scripts_dir = Path(__file__).parent  # Diretório atual (scripts)
    processing_dir = scripts_dir / "processing"
    plotting_dir = scripts_dir / "plotting"
    
    # Lista de scripts para executar
    pipeline_steps = [
        {
            'script': processing_dir / "process_ssh_data.py",
            'description': "PROCESSAMENTO DOS DADOS SSH",
            'essential': True
        },
        {
            'script': plotting_dir / "create_ssh_maps.py",
            'description': "CRIAÇÃO DE MAPAS ESTÁTICOS",
            'essential': False
        },
        {
            'script': plotting_dir / "create_ssh_animation.py",
            'description': "CRIAÇÃO DE ANIMAÇÕES",
            'essential': False
        }
    ]
    
    # Executar pipeline
    successful_steps = 0
    total_start_time = time.time()
    
    for i, step in enumerate(pipeline_steps, 1):
        print(f"\n🔄 PASSO {i}/{len(pipeline_steps)}")
        
        success = run_script(step['script'], step['description'])
        
        if success:
            successful_steps += 1
            print(f"✅ Passo {i} concluído com sucesso!")
        else:
            print(f"❌ Passo {i} falhou!")
            
            if step['essential']:
                print("🚨 Este passo é essencial. Parando pipeline.")
                break
            else:
                print("⚠️ Passo opcional falhou. Continuando...")
        
        # Pausa entre scripts
        if i < len(pipeline_steps):
            print("⏸️ Pausa de 2 segundos...")
            time.sleep(2)
    
    # Resumo final
    total_time = time.time() - total_start_time
    
    print(f"\n{'='*60}")
    print("📊 RESUMO DO PIPELINE")
    print(f"{'='*60}")
    print(f"✅ Passos concluídos: {successful_steps}/{len(pipeline_steps)}")
    print(f"⏱️ Tempo total: {total_time/60:.1f} minutos")
    
    if successful_steps == len(pipeline_steps):
        print("\n🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
        print("🗺️ Mapas e animações prontos para apresentação!")
        
        # Mostrar arquivos gerados
        figures_dir = Path(__file__).parent.parent.parent / "figures"
        if figures_dir.exists():
            files = list(figures_dir.glob("*"))
            print(f"\n📁 Arquivos gerados ({len(files)}):")
            for file in sorted(files):
                size_mb = file.stat().st_size / 1024**2
                print(f"   📄 {file.name} ({size_mb:.1f} MB)")
        
        print(f"\n🎯 PRONTO PARA O WAVES WORKSHOP!")
        
    elif successful_steps > 0:
        print("\n⚠️ Pipeline parcialmente concluído.")
        print("🔧 Verifique os erros e execute novamente.")
        
    else:
        print("\n❌ Pipeline falhou completamente.")
        print("🔧 Verifique o ambiente e dados de entrada.")
    
    print(f"\n📁 Resultados em: {Path(__file__).parent.parent.parent}")

if __name__ == "__main__":
    main()