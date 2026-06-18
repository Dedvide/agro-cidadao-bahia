# Camada 1 — Ontologia Agropecuária

Parte do **Bahia Agro Inteligente / SIPA-Bahia AI**. É a **espinha dorsal de dados**:
modela as entidades do mundo real do agronegócio baiano e suas relações, para que dados de
fontes diferentes (CETAB, ADAB, INEMA, IBGE, INMET, Embrapa) sejam cruzados de forma coerente.

## Propósito
Hoje os dados do SIPA vivem em ilhas (laudo tem `municipio` como texto solto; biotecnologia,
projetos e análises não se conectam). A ontologia dá uma **identidade única (UUID)** a cada
entidade, **relações tipadas** entre elas e **auditoria + origem multi-fonte** — permitindo
perguntas que cruzam domínios, como a **Ficha 360 do Município**.

Decisões de design (conforme especificação):
- Pydantic puro, **agnóstico de banco** (sem ORM ainda).
- `id` UUID em toda entidade; auditoria `created_at`/`updated_at` (UTC) + `source`.
- `origin_system` em toda entidade (suporte a múltiplas fontes).
- Geolocalização em **GeoJSON**; datas com timezone (**UTC**).
- Campos em `snake_case` (inglês); docstrings em português.

## Diagrama textual das relações

```
Municipio ─1──*─ Produtor
Municipio ─1──*─ Propriedade
Produtor  ─1──*─ Propriedade
Propriedade ─1──1─ Solo
Propriedade ─1──*─ AnaliseLaboratorial
Propriedade ─*──*─ Cultura            (culture_ids)
Cultura     ─*──*─ PragaDoenca        (host_culture_ids)
EventoSanitario ─*──1─ Municipio
EventoSanitario ─*──1─ Cultura
EventoSanitario ─*──1─ PragaDoenca
ProjetoPesquisa ─*──*─ Pesquisador    (researcher_ids)
ProjetoPesquisa ─*──*─ Cultura        (culture_ids)
FonteDados      ─alimenta→ AnaliseLaboratorial, EventoSanitario
```

## Estrutura
```
ontology/
  base.py            # BaseEntity (UUID, auditoria, origin_system), GeoJSON, enums
  territorio.py      # Municipio, Propriedade
  atores.py          # Produtor, Pesquisador
  ciencia.py         # Cultura, Solo, PragaDoenca, AnaliseLaboratorial, ProjetoPesquisa
  eventos.py         # EventoSanitario
  infraestrutura.py  # FonteDados
  registry.py        # Ontology (container) + municipio_360 (Ficha 360 / Digital Twin lite)
  linker.py          # liga laudos do SIPA → AnaliseLaboratorial (resolve Município por IBGE)
  fixtures.py        # seeds de exemplo + demonstração
```

## Como rodar a demonstração
A partir da raiz do projeto (`IaCetab/`):
```powershell
python -m ontology.fixtures
```
Mostra as entidades, a **Ficha 360 de Barreiras** e o **linker** convertendo um laudo do SIPA.

## Como adicionar novas entidades no futuro
1. Crie a classe no módulo de domínio adequado, herdando de `BaseEntity`
   (ganha UUID, auditoria e `origin_system` de graça).
2. Modele as **relações como campos tipados** por UUID: `<entidade>_id: uuid.UUID`
   (1:1 / N:1) ou `<entidade>_ids: list[uuid.UUID]` (N:N).
3. Marque os campos obrigatórios sem default; valide o resto com `Field(...)`.
4. Exporte a classe em `__init__.py`.
5. Se a entidade entrar em consultas cruzadas, estenda o `registry.py`.

## Próximos passos (integração com o SIPA)
- **Linker em produção:** percorrer os laudos reais (`prototipo-extrator`) e materializar
  `AnaliseLaboratorial` + `Propriedade` + `Municipio` (âncora: código IBGE já usado no mapa).
- **Ficha 360 na web:** expor `municipio_360` como uma tela (Digital Twin territorial — Camada 3).
- **Persistência:** quando estabilizar, mapear para PostgreSQL (a ontologia já está pronta para isso).
