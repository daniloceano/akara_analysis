# Atualização: Conversão de Longitude

## Mudanças Implementadas

### Problema Identificado
Os dados de espectro de ondas dos satélites CFOSAT SWIM e Sentinel-1A SAR originalmente usavam longitude no formato 0-360°. Para análises regionais, especialmente na região do ciclone Akará no Atlântico Sul (50°W a 30°W), era necessário converter para o formato -180 a 180°.

### Solução Implementada

**Scripts Modificados:**

1. **`analyze_wave_spectra.py`**
   - Adicionada conversão de longitude em 3 funções:
     - `analyze_dataset()` (método da classe SpectraAnalyzer)
     - `analyze_swim_data()`
     - `analyze_sar_data()`
   - Conversão: `lon = lon - 360 if lon > 180`

2. **`analyze_akara_spectra.py`**
   - Simplificada a função `filter_akara_region()`
   - Removida conversão duplicada (agora os dados já vêm no formato correto)
   - Filtro direto usando longitude em -180 a 180

### Validação

**Script de Teste: `test_longitude_conversion.py`**

Testes realizados:
1. ✅ Verificação que não há longitude > 180° nos dados SWIM
2. ✅ Verificação que não há longitude > 180° nos dados SAR
3. ✅ Validação que todos os dados da região Akará estão dentro dos limites corretos
4. ✅ Confirmação de dados no hemisfério ocidental (longitude negativa)

**Resultados:**
- SWIM: 35,672 registros, longitude -179.99° a 180.00°
- SAR: 6,080 registros, longitude -179.98° a 179.97°
- Região Akará SWIM: 418 registros, todos dentro dos limites -50° a -30°W
- Região Akará SAR: 95 registros, todos dentro dos limites -50° a -30°W

### Impacto nos Dados

**Arquivos CSV Atualizados:**
- `data/swim_analysis_results.csv` - Longitude em formato -180 a 180
- `data/sar_analysis_results.csv` - Longitude em formato -180 a 180
- `data/swim_akara_region.csv` - Dados filtrados corretamente para região Akará
- `data/sar_akara_region.csv` - Dados filtrados corretamente para região Akará

**Figuras:**
- Todas as visualizações foram regeneradas com longitude no formato correto
- Mapas agora mostram corretamente a localização dos dados no Atlântico Sul

### Benefícios

1. **Compatibilidade com convenções padrão**: O formato -180 a 180 é o padrão usado pela maioria das ferramentas de mapeamento e análise oceanográfica

2. **Filtros regionais corretos**: A região do Akará (longitude negativa) agora é filtrada corretamente sem conversões adicionais

3. **Consistência**: Todos os arquivos de saída usam o mesmo sistema de coordenadas

4. **Interoperabilidade**: Os dados podem ser facilmente integrados com outras fontes de dados oceanográficos

### Como Usar

Todos os scripts agora funcionam automaticamente com o formato correto:

```bash
# Análise completa (já com conversão de longitude)
python scripts/analyze_wave_spectra.py

# Análise focada na região Akará (sem necessidade de conversão adicional)
python scripts/analyze_akara_spectra.py

# Teste de validação
python scripts/test_longitude_conversion.py
```

### Documentação Atualizada

- `WAVE_SPECTRA_README.md` - Incluída explicação sobre conversão de longitude
- `WAVE_SPECTRA_ANALYSIS_SUMMARY.txt` - Atualizado com valores corretos de longitude

## Notas Técnicas

**Fórmula de Conversão:**
```python
lon = lon - 360 if lon > 180 else lon
```

**Por que isso funciona:**
- Longitude 0-180° (hemisfério leste) permanece inalterada
- Longitude 181-360° (hemisfério oeste) é convertida para -179 a 0°
- Exemplo: 315° → -45° (oeste do meridiano de Greenwich)

**Aplicação nos dados:**
- Dados originais: 0° a 360°
- Dados processados: -180° a 180°
- Região Akará: -50° a -30° (equivalente a 310° a 330° no formato antigo)
