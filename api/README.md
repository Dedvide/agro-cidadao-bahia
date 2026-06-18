# API — Hub Estadual de Inteligência Agropecuária da Bahia (R1)

Backend **FastAPI** que expõe o Data Lake + a Ontologia como **API REST**, decouplando a web
dos arquivos estáticos. É a peça-chave (R1 da auditoria) que destrava CRM, MDM, segurança e BI.

**Não duplica** lógica: reusa `prototipo-extrator/consultar.py` e o pacote `ontology/`.

## Como rodar

```powershell
# 1. garantir que há dados no Data Lake (uma vez)
cd ..\prototipo-extrator
python gerar_painel_demo.py

# 2. instalar e subir a API
cd ..\api
pip install -r requirements.txt
uvicorn main:app --reload
# abra http://127.0.0.1:8000/docs  (documentação interativa)
```

## Endpoints

| Método | Rota | O que retorna |
|---|---|---|
| GET | `/health` | status do serviço |
| GET | `/laudos?municipio=&categoria=&limite=` | lista de laudos |
| GET | `/laudos/{id}` | um laudo + resultados interpretados |
| GET | `/resumo` | resumo do Data Lake |
| GET | `/indicadores` | KPIs/cobertura/séries (dashboard) |
| GET | `/amostras.geojson` | amostras georreferenciadas (mapa) |
| GET | `/municipios` | municípios na ontologia |
| GET | `/municipios/{ibge}/ficha360` | **Ficha 360** (Digital Twin lite) |
| GET | `/ontologia/linhagem` | linhagem por `origin_system` |
| GET | `/integracoes` | catálogo de integração |

## Próximos passos (sobre esta base)
- **R2:** trocar SQLite → PostgreSQL/PostGIS (mudar só `servico._conn`).
- **R4:** OAuth2/RBAC + LGPD (middleware de auth + escopos por papel).
- Apontar as telas do `painel/` para a API (substituir `fetch("*.json")` por `fetch(API_URL+...)`).
