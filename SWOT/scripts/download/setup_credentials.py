#!/usr/bin/env python3
"""
Script de configuração para credenciais NASA Earthdata
Facilita a configuração inicial do ambiente para download de dados SWOT

Autor: Danilo Couto de Souza
Data: Setembro 2025
"""

import os
import getpass
from pathlib import Path

def create_netrc_file():
    """Cria arquivo .netrc com credenciais NASA Earthdata."""
    netrc_path = Path.home() / '.netrc'
    
    print("Configuração de Credenciais NASA Earthdata")
    print("==========================================")
    print("Você precisa de uma conta em: https://urs.earthdata.nasa.gov/")
    print()
    
    username = input("Digite seu username NASA Earthdata: ")
    password = getpass.getpass("Digite sua senha: ")
    
    netrc_content = f"""machine urs.earthdata.nasa.gov
login {username}
password {password}

machine podaac-tools.jpl.nasa.gov
login {username}
password {password}

machine cmr.earthdata.nasa.gov
login {username}
password {password}

machine n5eil01u.ecs.nsidc.org
login {username}
password {password}
"""
    
    try:
        with open(netrc_path, 'w') as f:
            f.write(netrc_content)
        
        # Definir permissões corretas (somente leitura para o usuário)
        os.chmod(netrc_path, 0o600)
        
        print(f"✓ Arquivo .netrc criado em: {netrc_path}")
        print("✓ Credenciais configuradas com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao criar arquivo .netrc: {e}")
        return False

def check_existing_credentials():
    """Verifica se credenciais já existem."""
    netrc_path = Path.home() / '.netrc'
    
    if netrc_path.exists():
        print(f"✓ Arquivo .netrc já existe em: {netrc_path}")
        
        response = input("Deseja sobrescrever? (y/N): ")
        return response.lower() == 'y'
    
    return True

def test_credentials():
    """Testa se as credenciais estão funcionando."""
    print("\nTestando credenciais...")
    
    try:
        import subprocess
        result = subprocess.run([
            'podaac-data-subscriber', 
            '-c', 'SWOT_L2_LR_SSH_Basic_2.0',
            '--dry-run'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Credenciais funcionando corretamente!")
            return True
        else:
            print("✗ Problema ao testar credenciais")
            print(f"Erro: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ Timeout no teste - mas credenciais podem estar OK")
        return True
    except Exception as e:
        print(f"✗ Erro no teste: {e}")
        return False

def install_podaac():
    """Oferece instalar o podaac-data-subscriber."""
    print("\nInstalação do podaac-data-subscriber")
    print("====================================")
    
    response = input("Deseja instalar o podaac-data-subscriber? (y/N): ")
    if response.lower() != 'y':
        return False
    
    try:
        import subprocess
        result = subprocess.run([
            'conda', 'install', '-c', 'conda-forge', 'podaac-data-subscriber', '-y'
        ], check=True)
        
        print("✓ podaac-data-subscriber instalado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro na instalação: {e}")
        print("Tente instalar manualmente: conda install -c conda-forge podaac-data-subscriber")
        return False

def main():
    """Função principal."""
    print("Setup para Download de Dados SWOT")
    print("=================================")
    
    # Verificar se podaac está instalado
    try:
        import subprocess
        subprocess.run(['podaac-data-subscriber', '--version'], 
                      capture_output=True, check=True)
        print("✓ podaac-data-subscriber já instalado")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("✗ podaac-data-subscriber não encontrado")
        if not install_podaac():
            print("Instale manualmente e execute este script novamente.")
            return
    
    # Configurar credenciais
    if check_existing_credentials():
        if create_netrc_file():
            test_credentials()
    
    print("\nConfiguração concluída!")
    print("Agora você pode executar: python download_swot_data.py")

if __name__ == "__main__":
    main()