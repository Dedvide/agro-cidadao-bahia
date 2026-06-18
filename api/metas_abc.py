"""
Metas do projeto ABC+ / PRODEAGRO (Ofício SEAGRI 464/2026).

Mistura dado AO VIVO (propriedades no CRM, análises no Data Lake) com contadores do
projeto (UDs, capacitados, eventos, SAFs%, recuperação%) editáveis em painel/metas-config.json.
Os alvos são os literais do Ofício.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "prototipo-extrator"))
CONFIG = RAIZ / "painel" / "metas-config.json"


def _config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {"uds_ilpf": 0, "capacitados": 0, "eventos": 0, "safs_pct": 0, "recuperacao_pct": 0,
            "uds_por_bioma": {}}


def metas() -> dict:
    import crm_repo
    import servico
    from municipios_bioma import ABC, bioma_de

    props = crm_repo.listar_propriedades()
    n_prop = len(props)
    try:
        conn = sqlite3.connect(servico._db())
        n_an = conn.execute(
            "SELECT COUNT(DISTINCT laudo_id) FROM laudo WHERE categoria_analise IN "
            "('fertilidade_solo','analise_agua')").fetchone()[0]
        conn.close()
    except Exception:
        n_an = 0

    c = _config()
    linhas = [
        {"meta": "Propriedades assistidas", "atual": n_prop, "alvo": 1000, "unidade": "propriedades", "fonte": "CRM (ao vivo)"},
        {"meta": "Análises de solo e água", "atual": n_an, "alvo": 1000, "unidade": "análises", "fonte": "Data Lake (ao vivo)"},
        {"meta": "Unidades demonstrativas ILPF", "atual": c["uds_ilpf"], "alvo": 3, "unidade": "UDs (1/bioma)", "fonte": "projeto"},
        {"meta": "Técnicos/produtores capacitados", "atual": c["capacitados"], "alvo": 800, "unidade": "pessoas", "fonte": "projeto"},
        {"meta": "Eventos de difusão", "atual": c["eventos"], "alvo": 30, "unidade": "eventos", "fonte": "projeto"},
        {"meta": "SAFs nas propriedades", "atual": c["safs_pct"], "alvo": 10, "unidade": "%", "fonte": "projeto"},
        {"meta": "Áreas degradadas recuperadas", "atual": c["recuperacao_pct"], "alvo": 30, "unidade": "%", "fonte": "projeto"},
    ]
    for m in linhas:
        m["pct"] = round(100 * m["atual"] / m["alvo"], 1) if m["alvo"] else 0

    por_bioma = {b: 0 for b in ABC}
    for p in props:
        b = bioma_de(p.get("municipio"))
        if b:
            por_bioma[b] += 1

    return {
        "projeto": "Aplicação Integrada do Plano ABC+ nos Biomas da Bahia — PRODEAGRO",
        "metas": linhas,
        "propriedades_por_bioma": por_bioma,
        "uds_por_bioma": c.get("uds_por_bioma", {}),
        "biomas": list(ABC.keys()),
    }
