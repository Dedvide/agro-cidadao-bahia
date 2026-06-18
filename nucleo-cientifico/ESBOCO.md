# Núcleo Científico (Módulo 11) — Esboço dos 3 sub-módulos

Os três se apoiam no mesmo Data Lake (dados estruturados + brutos + proveniência)
já construído no [prototipo-extrator](../prototipo-extrator/).

```
                    ┌──────────────── Data Lake (PostgreSQL/PostGIS) ────────────────┐
                    │  resultados estruturados · sinais brutos · proveniência         │
                    └───────┬─────────────────────┬───────────────────────┬──────────┘
                            │                     │                       │
                 (A) RAG Científico     (B) Relatório/Figuras     (C) Bibliometria
                 pergunta→resposta      dataset→artigo            produção→indicadores
                 + publicações                                    (Lattes/ORCID/DOI)
```

---

## (A) RAG Científico — assistente que responde sobre dados + publicações

**Objetivo:** o pesquisador pergunta em linguagem natural e recebe resposta fundamentada
nos **dados internos** do CETAB **e** na **literatura** (publicações do CETAB, Embrapa, MAPA).

### Arquitetura (RAG híbrido)
```
Pergunta
   │
   ├─► Roteador decide a fonte:
   │      • dado numérico/série  → Text-to-SQL sobre o Data Lake (resposta exata)
   │      • conhecimento/contexto → busca vetorial no corpus (publicações)
   │
   ├─► Recuperação
   │      • SQL: agrega/filtra resultados (ex.: "positividade de HLB por município em 2025")
   │      • Vetorial: top-k trechos de artigos (Qdrant/pgvector) + metadados (DOI, autor)
   │
   └─► Síntese (LLM) → resposta + CITAÇÃO da fonte (linha do dado OU DOI do artigo)
```

### Por que híbrido (e não só vetorial)
Pergunta sobre **número** ("qual a média de fósforo em Cruz das Almas?") exige consulta
**exata** ao banco — RAG vetorial alucina números. Pergunta sobre **conceito** ("qual o
manejo recomendado para meleira?") usa o corpus. O roteador escolhe.

### Componentes
| Peça | Tecnologia |
|---|---|
| Embeddings + índice | pgvector (ou Qdrant) sobre trechos de publicações |
| Text-to-SQL | LLM com o esquema do Data Lake no prompt (saída validada) |
| Corpus | PDFs/abstracts de publicações + base Embrapa/MAPA/AGROFIT |
| Síntese | LLM open-source local (soberania) |

### Guarda-corpos
- **Toda resposta cita a fonte** (linha do dado ou DOI). Sem fonte → "não sei".
- Números **sempre** do SQL, nunca "lembrados" pelo modelo.
- Stub wired em [`rag_cientifico.py`](rag_cientifico.py).

---

## (B) Gerador de Relatório/Figuras para artigos — IMPLEMENTADO

**Objetivo:** de um filtro do Data Lake → figuras publicáveis + rascunho de seções
("Material e Métodos", "Resultados") + estatística descritiva. Reduz semanas de trabalho braçal.

### Fluxo
```
filtro (eixo/analito/período) → dataset → [estatística + matplotlib] → figuras PNG
                                                                      → relatorio.md (rascunho)
```

### O que gera (ver [`gerar_relatorio.py`](gerar_relatorio.py))
- **Figuras**: série temporal de laudos, taxa de alerta por eixo, distribuição de classes,
  dispersão geográfica das amostras.
- **Rascunho .md**: descrição dos dados (n, período, eixos), parágrafo de métodos,
  tabela de estatística descritiva, figuras embutidas.
- **Proveniência** herdada do dataset (reprodutibilidade).

### Guarda-corpos
- IA **monta o rascunho**, o pesquisador escreve/valida. Números vêm do dado, não do modelo.

---

## (C) Painel Bibliométrico (Lattes/ORCID/DOI) — núcleo IMPLEMENTADO com dados reais

**Objetivo:** reconstruir e exibir a produção científica do CETAB — exatamente a lacuna
do estudo inicial (*"não há repositório público com DOI e métricas"*).

### Fontes e integração
| Fonte | O que traz | Integração |
|---|---|---|
| **Lattes (CNPq)** | currículo, publicações, orientações | Exportação XML / scraping (sem API oficial) |
| **ORCID** | identificador único + obras | **API pública** |
| **Crossref / OpenAlex** | metadados de DOI + **contagem de citações** | **API pública** |

### Fluxo
```
pesquisadores do CETAB → coleta (Lattes XML + ORCID) → deduplica por DOI
   → enriquece com Crossref/OpenAlex (citações, periódico, Qualis*)
   → indicadores: nº publicações, por ano, por periódico, citações, h-index
```
\* Qualis exige base CAPES (semestral).

### O que já roda (ver [`bibliometria.py`](bibliometria.py))
Calcula indicadores a partir de [`publicacoes_seed.json`](publicacoes_seed.json) — semeado
com os **DOIs reais** levantados na primeira conversa. A integração viva (ORCID/Crossref)
substitui o seed sem mudar o cálculo.

### Guarda-corpos
- Vínculo autor↔CETAB precisa de **validação** (parte da produção aparece sob Embrapa/UFRB/UFBA).
- Citações vêm de fonte rastreável (Crossref/OpenAlex), nunca estimadas.

---

## Encaixe nas fases
- (B) e (C) são **quick wins** — rodam sobre o que já existe, ótimos para o pitch.
- (A) é **Fase 3** — exige corpus indexado + infra vetorial.
