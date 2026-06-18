# Auditoria + GAP Analysis — Hub Estadual de Inteligência Agropecuária da Bahia
### CETAB · ADAB · SEAGRI (núcleo) · v1.0 · 2026-06-15

> **Escopo deste documento (honesto):** o prompt pede 10 camadas, governança, DevOps,
> PMO e 20 entregáveis. Isso é um **programa de 6 meses (MVP) + 3 anos** — exatamente o
> que o *Termo Institucional Bahia Agro Intelligence* já escopa (≈R$850 mil no Ano 1).
> Não se "implementa" num passo. O próprio prompt manda **auditar antes de mexer em código**.
> Este documento entrega as **Etapas 1 e 2 (Auditoria + GAP/Palantir)** + backlog priorizado
> + roadmap — a fundação para decidir os incrementos. Construir 10 camadas de uma vez seria
> o anti-padrão "ferver o oceano".

---

## 0. Reconciliação de fontes (3 visões convergentes)

| Fonte | O que define | Relação |
|---|---|---|
| **Protótipo atual** (este repo) | 46 módulos rodando (PoC) | o que **já existe** |
| **Termo Institucional "Bahia Agro Intelligence"** (Quantum Nexus + CETAB) | 4 camadas, 8 módulos, ontologia, governança, IP, minuta jurídica, MVP 6m | o **frame institucional/legal** |
| **Ofício SEAGRI 464/2026 (Projeto ABC+ / PRODEAGRO)** | Fundação ADM (executora), 3 biomas, 1.000 propriedades, Painel do Agricultor, lab. de Solos (43 anos) | o **projeto real com recurso** |
| **Este prompt (Hub, 10 camadas)** | alvo arquitetural detalhado inspirado em Palantir | a **arquitetura-alvo** |

**Achado-chave:** o `ontology/` que já construímos **é a implementação do Anexo C do Termo
Institucional** (módulos Território/Atores/Ciência/Eventos/Infraestrutura, UUID, auditoria,
`origin_system`, Pydantic, agnóstico de banco). Não duplicar — está feito.

---

## ETAPA 1 — AUDITORIA DA ARQUITETURA ATUAL

### Inventário real (varredura do código)
- **46 módulos Python** (~3.707 linhas) · **18 arquivos web** · 4 áreas:
  - `prototipo-extrator/` — núcleo: extração IA, Data Lake (SQLite), LIMS, QA/QC, importador em lote
  - `ontology/` — Camada 1 Ontologia + Data Fabric + Linker + materializador
  - `painel/` — 8 telas web (Dashboard, Laudos IA, Assistente, Ficha 360, LIMS, Centro, Integrações, Apresentação)
  - `nucleo-cientifico/` — RAG, bibliometria, gerador de relatório

### Arquitetura atual (camadas técnicas)
| Dimensão | Estado atual | Maturidade |
|---|---|---|
| **Backend** | Python + Pydantic, sem framework web (sem FastAPI) | PoC |
| **Frontend** | HTML estático + Leaflet + Chart.js (sem framework) | PoC |
| **Banco** | **SQLite** (arquivos) | PoC — produção = PostgreSQL/PostGIS |
| **APIs** | nenhuma exposta (geradores escrevem JSON; web lê arquivos) | ❌ |
| **Integrações** | catálogo + 1 conexão real ao vivo (IBGE) | ◑ |
| **Segurança** | selo de integridade de laudo (hash); sem auth/RBAC/LGPD técnica | ◑/❌ |
| **Infra** | scripts `.bat` locais; sem Docker/cloud | ❌ |
| **IA** | extração+interpretação (Claude), RAG TF-IDF, descoberta estatística | ◑ |

### Riscos técnicos identificados
1. **Sem API/backend** → web e dados acoplados a arquivos; não escala, não multiusuário. *(crítico)*
2. **SQLite** → sem concorrência, sem geo nativo, sem RBAC. *(crítico p/ produção)*
3. **Faixas de referência ilustrativas** → não são as oficiais do CETAB. *(crítico p/ uso real)*
4. **Sem governança de dados** (DAMA), sem catálogo/linhagem formal além de `origin_system`. *(importante)*
5. **Sem segurança de produção** (LGPD técnica, OAuth2, MFA, auditoria de acesso). *(crítico p/ órgão público)*
6. **Dependência de chave externa** (Claude) para extração → conflito com soberania de dados sensíveis. *(importante)*
7. **Arquivo órfão** `_lab_extract.txt` na raiz (sobra de pesquisa). *(trivial — limpar)*

---

## ETAPA 2 — GAP ANALYSIS (10 camadas-alvo × o que já existe)

> Legenda: ✅ feito (PoC) · ◑ parcial · ❌ ausente. **A coluna "Não duplicar" é a mais importante.**

| # | Camada-alvo (prompt) | Já existe? | Onde (não duplicar) | Falta para produção |
|---|---|---|---|---|
| 1 | **Data Fabric** (conectores, ETL, streaming) | ◑ | `ontology/data_fabric.py`, `importar_lote.py`, catálogo `integracoes` | conectores reais (SIDAB, INMET, MAPBIOMAS), streaming/event-driven |
| 2 | **Data Lake** (PDFs, imagens, laudos, versionamento) | ◑ | `persistencia.py` (SQLite), `repositorio.py` | object storage, versionamento, catálogo, linhagem |
| 3 | **Data Warehouse** analítico | ❌ | — | modelagem dimensional, separação OLTP/OLAP |
| 4 | **Ontologia Agropecuária** | ✅ | **`ontology/`** (11 entidades, UUID, auditoria) = Anexo C do Termo | + entidades Talhão, Bacia, Inspeção, Fiscalização; persistir em Postgres |
| 5 | **MDM** (cadastro mestre, dedup) | ❌ | seed: códigos IBGE no mapa; `Municipio` na ontologia | golden records, dedup produtor/propriedade |
| 6 | **CRM governamental** | ❌ | — | módulo de atendimentos/demandas |
| 7 | **Business Intelligence** | ◑ | `painel/` (6 dashboards, Chart.js) | Metabase/Superset sobre DW; KPIs oficiais |
| 8 | **GIS** | ◑ | mapa real da Bahia (IBGE), GeoJSON, Leaflet | **PostGIS + GeoServer**; camadas temáticas reais |
| 9 | **Digital Twin** territorial | ◑ | `registry.municipio_360` + `ficha360.html` | atualização contínua, feeds reais |
| 10a | **IA Científica (RAG)** | ◑ | `nucleo-cientifico/rag_cientifico.py`, `repositorio.py` | embeddings + pgvector/Qdrant (hoje TF-IDF) |
| 10b | **IA Laboratorial** | ✅ | `extrator.py` + `interpretar.py` | tabelas oficiais; modelo local (soberania) |
| 10c | **IA Preditiva** | ◑ | `descoberta.py` (correlações), scaffold pragas | modelos treinados (precisa histórico real) |
| 10d | **IA Geoespacial** | ◑ | `monitoramento_ambiental.py` (stubs INMET/SATVeg) | integração viva + visão de satélite |
| 10e | **IA Executiva** | ◑ | `gerar_relatorio.py`, `assistente` | geração de parecer com citação/governança |

**Resumo do GAP:** dos 10 blocos, **~6 já existem em PoC** (Ontologia, IA laboratorial,
Data Fabric, BI, GIS, Digital Twin — graus variados). **Os verdadeiros vazios são:**
Data Warehouse, **MDM**, **CRM**, e toda a **camada de produção** (backend/API, Postgres/PostGIS,
segurança, DevOps, governança).

### Comparação com plataformas de referência
| Capacidade Palantir/mercado | Hub hoje | Classificação do gap |
|---|---|---|
| Ontologia + objetos do mundo real (Foundry) | ✅ PoC | — (feito) |
| Pipelines/lineage versionados (Foundry) | ◑ `origin_system` | **Importante** |
| AIP / agentes sobre ontologia (Palantir AIP) | ◑ RAG+assistente | **Importante** |
| Catálogo + governança (Fabric/Databricks Unity) | ❌ | **Crítico** |
| Lakehouse (Databricks) | ◑ SQLite | **Crítico** |
| GIS empresarial (ArcGIS/GeoServer) | ◑ Leaflet | **Importante** |
| Segurança/RBAC/auditoria GovTech | ❌ | **Crítico** |
| Gotham (análise investigativa/grafos) | ❌ | **Desejável** (não é o caso de uso) |

---

## ETAPA 3+ — RECOMENDAÇÕES PRIORIZADAS (backlog)

> Formato exigido pelo prompt: justificativa · impacto · prioridade · esforço · risco · benefício.
> Esforço em pessoa-semana (PS) aproximado.

| Item | Justificativa | Impacto | Prio | Esforço | Risco se não fizer | Benefício |
|---|---|---|---|---|---|---|
| **R1. Backend/API (FastAPI)** | Hoje não há API; web lê arquivos. Sem isso nada vira multiusuário/produção. | Alto | 🔴 Crítico | 3–4 PS | Sistema trava em PoC | Destrava CRM, MDM, segurança, web real |
| **R2. PostgreSQL + PostGIS** | SQLite não serve produção nem GIS nativo. | Alto | 🔴 Crítico | 2–3 PS | Sem concorrência/geo/RBAC | Base sólida p/ todas as camadas |
| **R3. Tabelas de referência oficiais (CETAB)** | Faixas hoje são ilustrativas → interpretação não confiável. | Alto | 🔴 Crítico | 1–2 PS (com CETAB) | Decisão errada com dado errado | Laudo interpretado válido |
| **R4. Segurança LGPD + OAuth2/RBAC + auditoria** | Órgão público com dado de produtor; exige LGPD por design. | Alto | 🔴 Crítico | 3 PS | Risco jurídico/vazamento | Conformidade + confiança |
| **R5. Endurecer Ontologia → Postgres + entidades faltantes** | Ontologia existe (PoC); falta persistir e Talhão/Bacia/Inspeção. | Médio | 🟠 Importante | 2 PS | Limita cruzamentos | Cumpre Anexo C do Termo em produção |
| **R6. Linker em produção (materializar acervo real)** | Já há `materializar.py`; falta rodar no acervo real. | Alto | 🟠 Importante | 2 PS | Dados continuam ilhados | 1ª base integrada de verdade |
| **R7. MDM (golden records, dedup)** | Sem cadastro mestre há retrabalho e duplicidade (citado no Termo). | Médio | 🟠 Importante | 3 PS | Duplicidade, baixa qualidade | Qualidade de dados (DAMA) |
| **R8. CRM governamental** | Gerir atendimentos a produtores/municípios. | Médio | 🟡 Desejável | 3 PS | Atendimento sem rastreio | Relacionamento institucional |
| **R9. RAG real (pgvector/Qdrant)** | Hoje TF-IDF; produção pede semântica. | Médio | 🟡 Desejável | 2 PS | RAG limitado | Assistente científico forte |
| **R10. DevOps (Docker, CI/CD, observabilidade)** | Hoje só `.bat`. | Médio | 🟠 Importante | 3 PS | Implantação frágil | Operação confiável |
| **R11. GIS empresarial (GeoServer + camadas)** | Leaflet ok p/ demo; produção pede serviço geo. | Médio | 🟡 Desejável | 3 PS | Geo limitado | Mapas temáticos reais |
| **R12. Data Warehouse + BI (Metabase/Superset)** | Dashboards atuais são estáticos. | Médio | 🟡 Desejável | 3 PS | Indicadores manuais | BI corporativo |

---

## Roadmap honesto (alinhado ao MVP de 6 meses do Termo)

```
MVP / Fase 3 (meses 3–4 do Termo)  →  R1+R2+R3+R4 (backend, Postgres/PostGIS, tabelas oficiais, segurança)
                                       + R6 (linker no acervo real) + endurecer o que já existe
Fase 4–5 (meses 5–6)               →  R5 (ontologia prod) + R10 (DevOps) + R7 (MDM) — piloto
Ano 2 (roadmap)                    →  R8 (CRM) + R9 (RAG real) + R11 (GeoServer) + R12 (DW/BI)
                                       + conectores SIDAB/INMET/MAPBIOMAS (Data Fabric real)
Ano 3                              →  Digital Twin contínuo, IA preditiva em produção, cobertura estadual
```

**Princípio (já é o do Termo, §3.3):** *conectar, não substituir; entregas incrementais com
valor visível.* Endurecer o PoC existente, **não reconstruir**.

---

## Entregáveis do prompt — status nesta auditoria

| # Entregável | Status | Onde |
|---|---|---|
| 1. Diagnóstico completo | ✅ | este doc (Etapa 1) |
| 2. GAP Analysis | ✅ | este doc (Etapa 2) |
| 3. Arquitetura Atual | ✅ | este doc |
| 4. Arquitetura Futura | ◑ esboço | este doc + Cap.4 do Termo |
| 5–13 (C4, dados, ontologia, IA, GIS, CRM, BI, MDM, PMO) | ◑/❌ | ontologia ✅ (`ontology/`); demais = follow-up dedicado |
| 14. Roadmap Executivo | ✅ | este doc |
| 15. Backlog | ✅ | tabela R1–R12 |
| 16–19 (migração, implantação, escala, segurança) | ❌ | follow-up (dependem da decisão R1–R4) |
| 20. Recomendações finais | ✅ | abaixo |

---

## Recomendações finais

1. **Não duplicar.** ~6 das 10 camadas já existem em PoC — especialmente a **Ontologia
   (= Anexo C do Termo)**. O trabalho é **endurecer**, não recriar.
2. **A decisão que destrava tudo é R1+R2** (backend FastAPI + PostgreSQL/PostGIS). Sem isso,
   CRM, MDM, segurança e BI não têm onde existir.
3. **Antes de qualquer produção, R3** (tabelas oficiais) e **R4** (LGPD/segurança) — são
   bloqueadores para órgão público.
4. **Reconciliar a governança institucional:** existe Termo com a Quantum Nexus (parceira
   privada, IP definido) e o projeto ABC+ com a Fundação ADM (executora). A arquitetura técnica
   deve respeitar essa moldura (titularidade dos dados = CETAB; código = parceiro).
5. **Sequência sugerida de incrementos:** R1 → R2 → R3 → R6 (materializar acervo) → R4 →
   R5/R7. Cada um é um entregável demonstrável (princípio do Termo).
6. **Limpeza:** remover `_lab_extract.txt` (sobra) e consolidar nomes ("SIPA-Bahia AI" no
   código vs "Bahia Agro Intelligence" no Termo vs "Hub" no prompt → adotar um nome oficial).
