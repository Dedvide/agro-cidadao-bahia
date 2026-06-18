"""
Camada de serviço da API — acesso a dados do Hub.

REUSA os módulos que já existem (sem duplicar lógica):
  - `consultar` (prototipo-extrator) para resumo/indicadores/geojson
  - `ontology` (Data Fabric + registry) para a Ficha 360 do município

Decoupla a web dos arquivos: a partir daqui, tudo vem por função, não por JSON estático.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "prototipo-extrator" / "saida"
PAINEL = RAIZ / "painel"
# habilita import dos módulos existentes
sys.path.insert(0, str(RAIZ / "prototipo-extrator"))
sys.path.insert(0, str(RAIZ))

_ONT = None  # cache da ontologia materializada


def _norm(s: str) -> str:
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


def _db() -> Path:
    for nome in ("datalake_painel.sqlite", "demo_secretario.sqlite", "centro.sqlite"):
        p = SAIDA / nome
        if p.exists():
            return p
    raise RuntimeError("Data Lake não encontrado. Rode: prototipo-extrator/gerar_painel_demo.py")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_db())
    c.row_factory = sqlite3.Row
    return c


# ───────────────────────── Laudos / Data Lake ─────────────────────────

def listar_laudos(municipio=None, categoria=None, limite=100) -> list[dict]:
    where, params = [], []
    if municipio:
        where.append("LOWER(municipio)=LOWER(?)"); params.append(municipio)
    if categoria:
        where.append("categoria_analise=?"); params.append(categoria)
    clausula = ("WHERE " + " AND ".join(where)) if where else ""
    conn = _conn()
    rows = conn.execute(
        f"""SELECT id, laudo_id, categoria_analise, tipo_amostra, municipio,
                   data_coleta, confianca_geral, status
            FROM laudo {clausula} ORDER BY id DESC LIMIT ?""",
        (*params, limite),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obter_laudo(laudo_pk: int) -> dict | None:
    conn = _conn()
    l = conn.execute("SELECT * FROM laudo WHERE id=?", (laudo_pk,)).fetchone()
    if not l:
        conn.close(); return None
    res = conn.execute(
        "SELECT rotulo, valor_exibicao, classe, recomendacao, alerta FROM resultado WHERE laudo_fk=?",
        (laudo_pk,)).fetchall()
    d = dict(l)
    d["resultados"] = [dict(r) for r in res]
    conn.close()
    return d


def resumo() -> dict:
    import consultar
    conn = _conn(); r = consultar.resumo(conn); conn.close(); return r


def indicadores() -> dict:
    import consultar
    conn = _conn()
    dados = consultar.exportar_indicadores(conn, SAIDA / "_api_indicadores.json")
    conn.close()
    return dados


def amostras_geojson() -> dict:
    import consultar
    conn = _conn()
    consultar.exportar_geojson(conn, SAIDA / "_api_amostras.geojson")
    conn.close()
    return json.loads((SAIDA / "_api_amostras.geojson").read_text(encoding="utf-8"))


# ───────────────────────── Ontologia / Ficha 360 ─────────────────────────

def _ontologia():
    """Materializa a ontologia uma vez (cache) via Data Fabric."""
    global _ONT
    if _ONT is None:
        from ontology.data_fabric import CETABLaudosConnector, DataFabric
        lista = json.loads((SAIDA / "ba-lista.json").read_text(encoding="utf-8"))
        ibge_map = {_norm(m["nome"]): str(m["id"]) for m in lista}
        fabric = DataFabric().register(CETABLaudosConnector(_db(), ibge_map))
        _ONT = (fabric, fabric.run())
    return _ONT


def municipios_ontologia() -> list[dict]:
    from ontology.territorio import Municipio
    _, o = _ontologia()
    return [{"ibge_code": m.ibge_code, "name": m.name, "region": m.region}
            for m in sorted(o.all(Municipio), key=lambda x: x.name)]


def ficha360(ibge_code: str) -> dict | None:
    from ontology.territorio import Municipio
    _, o = _ontologia()
    mun = next((m for m in o.all(Municipio) if m.ibge_code == ibge_code), None)
    if not mun:
        return None
    f = o.municipio_360(mun.id)
    return {
        "municipio": {"name": mun.name, "ibge_code": mun.ibge_code, "region": mun.region},
        "propriedades": [{"name": p.name} for p in f["propriedades"]],
        "analises": [{
            "analysis_type": a.analysis_type, "laboratory": a.laboratory,
            "collected_at": a.collected_at.date().isoformat() if a.collected_at else None,
            "result": a.result, "external_ref": a.external_ref, "origin_system": a.origin_system,
        } for a in f["analises"]],
        "eventos": [{"event_type": e.event_type, "status": e.status.value,
                     "occurred_at": e.occurred_at.date().isoformat(), "origin_system": e.origin_system}
                    for e in f["eventos_sanitarios"]],
    }


def linhagem() -> list[dict]:
    fabric, _ = _ontologia()
    return [{"origin_system": s, "n": n} for s, n in fabric.lineage()]


def integracoes() -> dict:
    p = PAINEL / "integracoes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"grupos": []}


# ───────────────────────── Centro de Operações ─────────────────────────

def operacoes_resumo() -> dict:
    """Estado operacional consolidado (sala de operações): KPIs, focos, alertas, pendências."""
    import crm_repo
    import metas_abc
    from municipios_bioma import ABC, bioma_de

    conn = sqlite3.connect(_db()); conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) FROM laudo").fetchone()[0]
    municipios = conn.execute("SELECT COUNT(DISTINCT municipio) FROM laudo").fetchone()[0]
    alertas = conn.execute("SELECT COUNT(*) FROM resultado WHERE alerta=1").fetchone()[0]
    focos = [dict(r) for r in conn.execute(
        """SELECT l.municipio municipio, r.alvo alvo FROM resultado r JOIN laudo l ON l.id=r.laudo_fk
           WHERE r.alvo IS NOT NULL AND r.resultado_diagnostico='positivo'""").fetchall()]
    alertas_lista = [dict(r) for r in conn.execute(
        """SELECT l.municipio municipio, r.rotulo rotulo, r.classe classe FROM resultado r
           JOIN laudo l ON l.id=r.laudo_fk WHERE r.alerta=1 ORDER BY l.id DESC LIMIT 12""").fetchall()]
    conn.close()

    props = crm_repo.listar_propriedades()
    atend = crm_repo.listar_atendimentos()
    pend = [a for a in atend if (a.get("status") or "") != "concluido"]
    por_bioma = {b: 0 for b in ABC}
    for p in props:
        b = bioma_de(p.get("municipio"))
        if b:
            por_bioma[b] += 1

    return {
        "kpis": {"laudos": total, "municipios": municipios, "alertas": alertas,
                 "propriedades": len(props), "pendencias": len(pend), "focos": len(focos)},
        "focos_sanitarios": focos,
        "alertas_recentes": alertas_lista,
        "pendencias": [{"propriedade_id": a["propriedade_id"], "problema": a.get("problema"),
                        "tecnico": a.get("tecnico"), "retorno_previsto": a.get("retorno_previsto")}
                       for a in pend[:10]],
        "propriedades_por_bioma": por_bioma,
        "metas": metas_abc.metas()["metas"],
    }


def clima(municipio: str) -> dict:
    """Clima + risco fitossanitário do município (fonte: monitoramento ambiental / APIs públicas)."""
    import monitoramento_ambiental as ma
    return ma.avaliar_municipio(municipio)
