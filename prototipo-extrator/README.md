# Protótipo — Extrator de Laudos com IA (SIPA-Bahia AI · Fase 2)

O **coração técnico** do sistema: pega um laudo em **qualquer formato** e devolve
dado **estruturado, validado e interpretado**, sinalizando incertezas para revisão
humana (a trilha de auditoria que o edital da ENAP valoriza).

```
laudo bagunçado  ──►  [ IA + esquema canônico ]  ──►  JSON estruturado  ──►  interpretação
 (txt, csv, ...)        saída estruturada forçada      validado (Pydantic)     + recomendação
```

## Por que isto é a peça central

Os dados do CETAB estão espalhados em Excel, Word e arquivos de máquina, **cada um
num layout diferente**. Regras fixas quebram nessa heterogeneidade. Um LLM amarrado
a um **JSON Schema** extrai de forma robusta mesmo com variação — e o score de
confiança decide o que vai para revisão humana.

## Cobre os 5 eixos do CETAB (3 tipos de resultado)

O esquema generaliza o resultado em três naturezas, cobrindo todos os eixos:

| Tipo | Eixos | Resultado |
|---|---|---|
| `quantitativo` | Solos, Água, Foliar, **Resíduos/Contaminantes**, **Qualidade de Alimentos** | analito + valor + unidade (ou vs. LMR) |
| `diagnostico` | **Biologia Molecular**, **Sanidade de Citros** | alvo (HLB/CVC) + positivo/negativo + Ct |
| `identificacao` | **Ecologia Química / Moscas-das-frutas**, Fitopatologia | espécie + contagem (nível de infestação) |

O mesmo pipeline (ingestão → IA → Data Lake → mapa) serve aos três.

## Arquivos

| Arquivo | Papel |
|---|---|
| `schema.py` | Esquema canônico (Pydantic) — a "língua única" do sistema |
| `extrator.py` | Extrator: documento (`.txt/.csv/.docx/.pdf`) → `Laudo` validado (Claude + tool use) |
| `limites_referencia.py` | Faixas de referência **ilustrativas** para interpretação |
| `interpretar.py` | Valor bruto → classe + recomendação (com explicabilidade) |
| `municipios_ba.py` | Centroides de municípios da BA → georreferenciamento |
| `persistencia.py` | **Data Lake** (SQLite no protótipo; PostgreSQL+PostGIS em produção) |
| `consultar.py` | Consolidação: resumo, distribuição de classes, export **GeoJSON** (mapa) |
| `run_demo.py` | Pipeline ponta a ponta: extrai → interpreta → grava → consolida → mapa |
| `exemplos/laudo_solo_01.txt` | Fertilidade de solo — texto, vírgula decimal |
| `exemplos/laudo_solo_02.csv` | Fertilidade de solo — CSV, layout diferente |
| `exemplos/laudo_solo_03.docx` | Fertilidade de solo — Word com tabela |
| `exemplos/laudo_agua_01.txt` | Qualidade da água (quantitativo) |
| `exemplos/laudo_residuos_01.csv` | Resíduos de agrotóxicos (quantitativo vs. LMR) |
| `exemplos/laudo_mel_01.txt` | Qualidade de alimentos — mel de cacau |
| `exemplos/laudo_molecular_hlb_01.txt` | Diagnóstico molecular HLB/CVC (diagnostico) |
| `exemplos/laudo_moscas_01.csv` | Monitoramento de moscas-das-frutas (identificacao) |
| `teste_offline.py`, `teste_persistencia.py`, `teste_loader_docx.py` | Testes **sem API** (esquema, Data Lake, loader .docx) |

Os exemplos são **de propósito em formatos diferentes** para provar que a IA normaliza
todos para a mesma estrutura.

### Testes que rodam sem chave de API
```powershell
python teste_offline.py        # esquema + interpretação
python teste_persistencia.py   # Data Lake + consolidação + GeoJSON
python teste_loader_docx.py    # leitura de .docx (parágrafos + tabela)
```

## Como rodar (Windows / PowerShell)

```powershell
cd prototipo-extrator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = 'sua-chave-aqui'
python run_demo.py
```

Para um único laudo:
```powershell
python extrator.py exemplos\laudo_solo_01.txt
```

Modelo configurável: `$env:CETAB_MODELO = 'claude-sonnet-4-6'` (padrão).

## O que é protótipo vs. produção

| Hoje (protótipo) | Produção (Fase 2 completa) |
|---|---|
| Lê `.txt/.csv/.docx/.pdf` | + `.cdf`/mzML de cromatógrafo; PDF escaneado via docling/OCR |
| Faixas de referência ilustrativas | Tabelas oficiais CETAB/Embrapa por método e cultura |
| Data Lake em SQLite + GeoJSON | PostgreSQL + PostGIS; painel/mapa web |
| Georreferencia por centroide de município | Coordenada real da amostra (GPS de coleta) |
| Claude API | Modelo open-source local (soberania de dados) |

## Próximos passos

1. Validar a extração com **laudos reais** do CETAB (quando o inventário chegar).
2. Ajustar o esquema canônico aos analitos que o CETAB de fato mede.
3. Plugar a saída no banco (Data Lake) e expor um painel.
