#!/usr/bin/env python3
"""
Buscar produtos SWOT de altura de onda
"""

import requests
import json
from datetime import datetime, timedelta

def search_swot_wave_products():
    """
    Buscar produtos SWOT relacionados a ondas no CMR (Common Metadata Repository)
    """
    
    print("🔍 BUSCANDO PRODUTOS SWOT DE ONDAS")
    print("="*60)
    
    # URL base do CMR da NASA
    cmr_base = "https://cmr.earthdata.nasa.gov/search/collections.json"
    
    # Termos de busca para produtos SWOT de ondas
    search_terms = [
        "SWOT L3 SSH",
        "SWOT L3 Wind", 
        "SWOT L3 Wave",
        "SWOT L2 HR PIXC",
        "SWOT L2 HR PIXCVec", 
        "SWOT SWS",
        "SWOT significant wave height",
        "SWOT wave height",
        "SWOT Hs",
        "SWOT L3 LR SSH"
    ]
    
    found_products = []
    
    for term in search_terms:
        print(f"\\n🔎 Buscando: {term}")
        
        try:
            params = {
                'keyword': term,
                'page_size': 10,
                'provider': 'POCLOUD'  # Physical Oceanography DAAC
            }
            
            response = requests.get(cmr_base, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                collections = data.get('feed', {}).get('entry', [])
                
                for collection in collections:
                    title = collection.get('title', 'Sem título')
                    summary = collection.get('summary', '')
                    concept_id = collection.get('id', '')
                    
                    # Verificar se é realmente relacionado a ondas
                    wave_keywords = ['wave', 'swh', 'significant', 'height', 'wind', 'ssh', 'surface']
                    if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() 
                           for keyword in wave_keywords):
                        
                        product_info = {
                            'title': title,
                            'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                            'concept_id': concept_id,
                            'search_term': term
                        }
                        
                        # Evitar duplicatas
                        if concept_id not in [p['concept_id'] for p in found_products]:
                            found_products.append(product_info)
                            print(f"  ✅ Encontrado: {title}")
                        
        except Exception as e:
            print(f"  ❌ Erro na busca '{term}': {e}")
            continue
    
    print(f"\\n📊 RESUMO: {len(found_products)} produtos encontrados")
    print("="*60)
    
    for i, product in enumerate(found_products, 1):
        print(f"\\n{i}. {product['title']}")
        print(f"   ID: {product['concept_id']}")
        print(f"   Busca: {product['search_term']}")
        print(f"   Resumo: {product['summary']}")
        
        # Verificar se tem dados temporais relevantes
        if 'concept_id' in product:
            try:
                granules_url = f"https://cmr.earthdata.nasa.gov/search/granules.json"
                granule_params = {
                    'collection_concept_id': product['concept_id'],
                    'page_size': 5,
                    'temporal': '2024-02-14T00:00:00Z,2024-02-22T23:59:59Z'
                }
                
                granule_response = requests.get(granules_url, params=granule_params, timeout=15)
                if granule_response.status_code == 200:
                    granule_data = granule_response.json()
                    granules = granule_data.get('feed', {}).get('entry', [])
                    print(f"   📅 Granules no período: {len(granules)}")
                    
                    if granules:
                        print(f"   📁 Exemplo: {granules[0].get('title', 'Sem título')}")
                        
            except:
                print(f"   📅 Não foi possível verificar granules")
    
    return found_products

def search_podaac_swot():
    """
    Buscar especificamente no catálogo PO.DAAC
    """
    print("\\n\\n🌊 BUSCANDO NO PO.DAAC (Physical Oceanography DAAC)")
    print("="*60)
    
    # URLs conhecidos de produtos SWOT no PO.DAAC
    known_products = [
        {
            'name': 'SWOT L2 LR SSH Basic',
            'description': 'SSH básico low-resolution'
        },
        {
            'name': 'SWOT L2 HR PIXC',
            'description': 'Pixel Cloud high-resolution - pode conter info de ondas'
        },
        {
            'name': 'SWOT L3 LR SSH',
            'description': 'SSH gridded - pode ter produtos derivados'
        },
        {
            'name': 'SWOT L2 HR PIXCVec', 
            'description': 'Pixel Cloud Vector - análises avançadas'
        }
    ]
    
    for product in known_products:
        print(f"\\n📦 {product['name']}")
        print(f"   {product['description']}")
        
    return known_products

if __name__ == "__main__":
    # Buscar produtos
    cmr_products = search_swot_wave_products()
    podaac_products = search_podaac_swot()
    
    print("\\n\\n🎯 PRÓXIMOS PASSOS:")
    print("="*60)
    print("1. Verificar produtos L2 HR PIXC - podem ter dados de ondas")
    print("2. Procurar produtos L3 derivados")
    print("3. Calcular altura de ondas a partir da SSH existente")
    print("4. Usar dados ERA5 como referência para validação")