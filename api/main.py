"""
API REST do Hub Estadual de Inteligência Agropecuária da Bahia (R1 — backend FastAPI).

Expõe o Data Lake + a Ontologia como serviço, decouplando a web dos arquivos estáticos.
Documentação interativa automática em /docs (OpenAPI/Swagger).

Rodar (da pasta api/):  uvicorn main:app --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import crm_repo
import metas_abc
import servico

PAINEL = Path(__file__).resolve().parent.parent / "painel"
from crm_models import AtendimentoIn, OcorrenciaIn, ProdutorIn, PropriedadeIn

app = FastAPI(
    title="Hub Estadual de Inteligência Agropecuária da Bahia — API",
    version="0.1.0",
    description="Camada de serviço (R1) sobre o Data Lake e a Ontologia. CETAB · ADAB · SEAGRI.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
def _runtime(_request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"erro": str(exc)})


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/app/")  # interface operacional unificada (/docs = API)


@app.get("/health", tags=["sistema"])
def health():
    return {"status": "ok", "servico": "Hub Bahia — API", "versao": app.version}


@app.get("/laudos", tags=["laudos"])
def laudos(municipio: str | None = None, categoria: str | None = None, limite: int = 100):
    """Lista laudos do Data Lake, com filtros opcionais por município e categoria."""
    return servico.listar_laudos(municipio, categoria, limite)


@app.get("/laudos/{laudo_pk}", tags=["laudos"])
def laudo(laudo_pk: int):
    """Um laudo com seus resultados interpretados."""
    d = servico.obter_laudo(laudo_pk)
    if not d:
        raise HTTPException(404, "laudo não encontrado")
    return d


@app.get("/resumo", tags=["indicadores"])
def resumo():
    return servico.resumo()


@app.get("/indicadores", tags=["indicadores"])
def indicadores():
    """Indicadores consolidados (KPIs, cobertura, séries) — alimenta o dashboard."""
    return servico.indicadores()


@app.get("/amostras.geojson", tags=["geo"])
def amostras_geojson():
    """Amostras georreferenciadas (GeoJSON) — alimenta o mapa."""
    return servico.amostras_geojson()


@app.get("/municipios", tags=["ontologia"])
def municipios():
    """Municípios presentes na ontologia (materializada do acervo)."""
    return servico.municipios_ontologia()


@app.get("/municipios/{ibge_code}/ficha360", tags=["ontologia"])
def ficha360(ibge_code: str):
    """Ficha 360 do município (Digital Twin lite): análises + eventos + propriedades."""
    d = servico.ficha360(ibge_code)
    if not d:
        raise HTTPException(404, "município sem dados na ontologia")
    return d


@app.get("/ontologia/linhagem", tags=["ontologia"])
def linhagem():
    """Linhagem dos dados (de qual sistema veio cada entidade)."""
    return servico.linhagem()


@app.get("/integracoes", tags=["integracoes"])
def integracoes():
    """Catálogo de integração com os entes (Embrapa, IBGE, ADAB, INMET...)."""
    return servico.integracoes()


# ───────────────────────── CRM (Camada Operacional) ─────────────────────────
# Onde os técnicos ALIMENTAM o sistema: cadastro, visita (prontuário), ocorrência.

@app.post("/crm/produtores", tags=["crm"], status_code=201)
def criar_produtor(p: ProdutorIn):
    return crm_repo.cadastrar_produtor(p.model_dump())


@app.get("/crm/produtores", tags=["crm"])
def produtores():
    return crm_repo.listar_produtores()


@app.post("/crm/propriedades", tags=["crm"], status_code=201)
def criar_propriedade(p: PropriedadeIn):
    return crm_repo.cadastrar_propriedade(p.model_dump())


@app.get("/crm/propriedades", tags=["crm"])
def propriedades():
    return crm_repo.listar_propriedades()


@app.post("/crm/atendimentos", tags=["crm"], status_code=201)
def criar_atendimento(a: AtendimentoIn):
    """Registra uma visita/orientação — alimenta o prontuário da propriedade."""
    return crm_repo.registrar_atendimento(a.model_dump())


@app.get("/crm/atendimentos", tags=["crm"])
def atendimentos():
    return crm_repo.listar_atendimentos()


@app.post("/crm/ocorrencias", tags=["crm"], status_code=201)
def criar_ocorrencia(o: OcorrenciaIn):
    return crm_repo.abrir_ocorrencia(o.model_dump())


@app.get("/crm/propriedades/{prop_id}/prontuario", tags=["crm"])
def prontuario(prop_id: int):
    """Prontuário eletrônico da propriedade: atendimentos + ocorrências + análises."""
    d = crm_repo.prontuario_propriedade(prop_id)
    if not d:
        raise HTTPException(404, "propriedade não encontrada")
    return d


@app.get("/crm/tecnicos/{tecnico}/carteira", tags=["crm"])
def carteira(tecnico: str):
    """Carteira digital do técnico (assistência técnica): produtores, visitas, pendências."""
    return crm_repo.carteira_tecnico(tecnico)


# ───────────────────────── Metas ABC+ / PRODEAGRO ─────────────────────────

@app.get("/abc/metas", tags=["abc+"])
def abc_metas():
    """Painel de metas do projeto ABC+ (Ofício SEAGRI): 6 indicadores + por bioma."""
    return metas_abc.metas()


@app.get("/operacoes/resumo", tags=["operacoes"])
def operacoes_resumo():
    """Centro de Operações: KPIs, focos sanitários, alertas, pendências, metas (ao vivo)."""
    return servico.operacoes_resumo()


@app.get("/clima/{municipio}", tags=["agricultor"])
def clima(municipio: str):
    """Clima + risco do município (fonte: monitoramento ambiental / APIs públicas)."""
    return servico.clima(municipio)


# ───────────────────────── Interface web unificada ─────────────────────────
# Serve o painel inteiro (dashboards + CRM operacional) na MESMA origem da API.
# /app/ = interface · /app/crm.html = portal operacional · /docs = API.
app.mount("/app", StaticFiles(directory=str(PAINEL), html=True), name="painel")
