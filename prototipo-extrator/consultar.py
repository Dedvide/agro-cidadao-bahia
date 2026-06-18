"""
Consolidação do Data Lake multi-eixo — o que vira VALOR e NÚMERO para a ENAP.

- resumo geral + por categoria de análise (os 5 eixos)
- status de cada amostra (requer atenção se tiver algum alerta)
- exportação GeoJSON uniforme → base do Mapa Inteligente da Bahia
- indicadores (cards do painel)
"""
from __future__ import annotations

import csv
import datetime
import json
import sqlite3
from pathlib import Path

from municipios_ba import centroide

# Dicionário de dados do dataset de pesquisa (acompanha cada exportação — FAIR).
DICIONARIO_DATASET = {
    "laudo_id": "Identificador do laudo de origem",
    "categoria_analise": "Eixo/tipo de análise (fertilidade_solo, diagnostico_molecular, ...)",
    "tipo_amostra": "Material analisado (solo, agua, foliar, fruto, mel, inseto, ...)",
    "municipio": "Município da amostra (Bahia)",
    "latitude": "Latitude (centroide do município no protótipo; GPS real em produção)",
    "longitude": "Longitude",
    "data_coleta": "Data da coleta (AAAA-MM-DD)",
    "solicitante_tipo": "Tipo de solicitante",
    "tipo_resultado": "quantitativo | diagnostico | identificacao",
    "rotulo": "Parâmetro/alvo/táxon medido",
    "analito": "Analito (resultado quantitativo)",
    "valor": "Valor numérico (quantitativo)",
    "unidade": "Unidade de medida",
    "alvo": "Patógeno pesquisado (diagnostico)",
    "resultado_diagnostico": "positivo | negativo | inconclusivo",
    "ct": "Cycle threshold (qPCR)",
    "taxon": "Espécie identificada (identificacao)",
    "contagem": "Nº de indivíduos (identificacao)",
    "classe": "Classe interpretada",
    "alerta": "1 se fora do ideal/conformidade",
    "metodo": "Método analítico",
    "confianca_extracao": "Confiança da extração por IA (0–1)",
}


def resumo(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM laudo").fetchone()[0]
    municipios = conn.execute(
        "SELECT municipio, COUNT(*) n FROM laudo GROUP BY municipio ORDER BY n DESC"
    ).fetchall()
    revisao = conn.execute("SELECT COUNT(*) FROM laudo WHERE confianca_geral < 0.7").fetchone()[0]
    por_categoria = conn.execute(
        "SELECT categoria_analise, COUNT(*) n FROM laudo GROUP BY categoria_analise ORDER BY n DESC"
    ).fetchall()
    # laudos com pelo menos um alerta
    alertas = conn.execute(
        "SELECT COUNT(DISTINCT laudo_fk) FROM resultado WHERE alerta = 1"
    ).fetchone()[0]
    return {
        "total_laudos": total,
        "municipios_cobertos": len(municipios),
        "por_municipio": [(r["municipio"], r["n"]) for r in municipios],
        "por_categoria": [(r["categoria_analise"], r["n"]) for r in por_categoria],
        "laudos_com_alerta": alertas,
        "aguardando_revisao_humana": revisao,
    }


def distribuicao_classe(conn: sqlite3.Connection, rotulo_ou_analito: str) -> list[tuple[str, int]]:
    """Distribuição de classes para um rótulo (ex.: 'fosforo','HLB')."""
    linhas = conn.execute(
        """SELECT COALESCE(classe, 'sem_classe') classe, COUNT(*) n
           FROM resultado WHERE LOWER(rotulo) = LOWER(?) GROUP BY classe ORDER BY n DESC""",
        (rotulo_ou_analito,),
    ).fetchall()
    return [(r["classe"], r["n"]) for r in linhas]


def _laudo_status(conn: sqlite3.Connection, laudo_id: int) -> str:
    n = conn.execute(
        "SELECT COUNT(*) FROM resultado WHERE laudo_fk = ? AND alerta = 1", (laudo_id,)
    ).fetchone()[0]
    return "requer_atencao" if n else "adequado"


def exportar_geojson(conn: sqlite3.Connection, destino: str | Path) -> int:
    laudos = conn.execute(
        """SELECT id, laudo_id, categoria_analise, municipio, tipo_amostra, latitude,
                  longitude, solicitante_tipo, data_coleta, confianca_geral
           FROM laudo WHERE latitude IS NOT NULL AND longitude IS NOT NULL"""
    ).fetchall()
    features = []
    for r in laudos:
        resultados = conn.execute(
            """SELECT tipo, rotulo, valor_exibicao, classe, recomendacao, alerta
               FROM resultado WHERE laudo_fk = ?""",
            (r["id"],),
        ).fetchall()
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
            "properties": {
                "laudo_id": r["laudo_id"],
                "categoria_analise": r["categoria_analise"],
                "municipio": r["municipio"],
                "tipo_amostra": r["tipo_amostra"],
                "solicitante_tipo": r["solicitante_tipo"],
                "data_coleta": r["data_coleta"],
                "confianca_geral": r["confianca_geral"],
                "status": _laudo_status(conn, r["id"]),
                "resultados": [
                    {
                        "tipo": rr["tipo"],
                        "rotulo": rr["rotulo"],
                        "valor": rr["valor_exibicao"],
                        "classe": rr["classe"],
                        "recomendacao": rr["recomendacao"],
                        "alerta": bool(rr["alerta"]),
                    }
                    for rr in resultados
                ],
            },
        })
    fc = {"type": "FeatureCollection", "features": features}
    Path(destino).write_text(json.dumps(fc, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(features)


def exportar_indicadores(conn: sqlite3.Connection, destino: str | Path) -> dict:
    """Indicadores ricos para o dashboard: KPIs ENAP, séries, recomendações, municípios."""
    dados = resumo(conn)
    total = dados["total_laudos"] or 1

    # por eixo com alertas
    cats = conn.execute(
        """SELECT l.categoria_analise cat, COUNT(DISTINCT l.id) n,
                  COUNT(DISTINCT CASE WHEN r.alerta = 1 THEN l.id END) alertas
           FROM laudo l LEFT JOIN resultado r ON r.laudo_fk = l.id
           GROUP BY l.categoria_analise ORDER BY n DESC"""
    ).fetchall()
    dados["por_categoria_detalhe"] = [
        {"categoria": c["cat"], "total": c["n"], "alertas": c["alertas"]} for c in cats
    ]

    # série temporal (laudos por mês)
    serie = conn.execute(
        """SELECT substr(data_coleta, 1, 7) mes, COUNT(*) n FROM laudo
           WHERE data_coleta IS NOT NULL GROUP BY mes ORDER BY mes"""
    ).fetchall()
    dados["serie_mensal"] = [[s["mes"], s["n"]] for s in serie]

    # municípios (para camada de bolhas): volume + alertas + centroide
    muns = conn.execute(
        """SELECT l.municipio mun, COUNT(DISTINCT l.id) n,
                  COUNT(DISTINCT CASE WHEN r.alerta = 1 THEN l.id END) alertas
           FROM laudo l LEFT JOIN resultado r ON r.laudo_fk = l.id
           WHERE l.municipio IS NOT NULL GROUP BY l.municipio"""
    ).fetchall()
    municipios = []
    for m in muns:
        lat, lon = centroide(m["mun"])
        if lat is None:
            continue
        municipios.append({
            "nome": m["mun"], "lat": lat, "lon": lon,
            "total": m["n"], "alertas": m["alertas"],
        })
    dados["municipios"] = municipios

    # feed de recomendações automáticas
    recs = conn.execute(
        """SELECT l.laudo_id lid, l.municipio mun, l.categoria_analise cat,
                  r.rotulo rotulo, r.recomendacao rec
           FROM resultado r JOIN laudo l ON l.id = r.laudo_fk
           WHERE r.recomendacao IS NOT NULL ORDER BY r.alerta DESC LIMIT 40"""
    ).fetchall()
    dados["recomendacoes"] = [
        {"laudo_id": r["lid"], "municipio": r["mun"], "categoria": r["cat"],
         "rotulo": r["rotulo"], "texto": r["rec"]} for r in recs
    ]

    # KPIs estilo ENAP
    af = conn.execute(
        "SELECT COUNT(*) FROM laudo WHERE solicitante_tipo = 'agricultura_familiar'"
    ).fetchone()[0]
    alertas_emitidos = conn.execute("SELECT COUNT(*) FROM resultado WHERE alerta = 1").fetchone()[0]
    dados["indicadores_enap"] = {
        "laudos_processados": dados["total_laudos"],
        "municipios_beneficiados": dados["municipios_cobertos"],
        "alertas_emitidos": alertas_emitidos,
        "agricultura_familiar": af,
        "pct_agricultura_familiar": round(100 * af / total),
        "taxa_alerta_pct": round(100 * dados["laudos_com_alerta"] / total),
        "tempo_estimado_economizado_h": round(dados["total_laudos"] * 0.5, 1),  # ~30min/laudo (estimativa)
    }

    dados["distribuicao_fosforo"] = distribuicao_classe(conn, "fosforo")
    dados["distribuicao_ph"] = distribuicao_classe(conn, "ph")

    # cobertura do estado (municípios atendidos vs. 417 da Bahia)
    dados["cobertura"] = {
        "com_dados": dados["municipios_cobertos"], "total_estado": 417,
        "pct": round(100 * dados["municipios_cobertos"] / 417, 1),
    }
    # por tipo de solicitante (foco agricultura familiar)
    dados["por_solicitante"] = [
        [r[0] or "nao_informado", r[1]] for r in conn.execute(
            "SELECT solicitante_tipo, COUNT(*) FROM laudo GROUP BY solicitante_tipo ORDER BY COUNT(*) DESC").fetchall()]
    # ranking de municípios por nº de laudos
    dados["ranking_municipios"] = dados["por_municipio"][:8]
    # positividade de diagnóstico molecular
    dados["diagnostico_positividade"] = [
        [r[0], r[1]] for r in conn.execute(
            "SELECT resultado_diagnostico, COUNT(*) FROM resultado WHERE tipo='diagnostico' "
            "GROUP BY resultado_diagnostico").fetchall()]
    # conformidade (resíduos/contaminantes)
    dados["conformidade"] = [
        [r[0], r[1]] for r in conn.execute(
            "SELECT classe, COUNT(*) FROM resultado WHERE classe IN ('conforme','acima do LMR') "
            "GROUP BY classe").fetchall()]

    Path(destino).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return dados


# ───────────────────────── Núcleo Científico (Módulo 11) ─────────────────────────

_COLUNAS_DATASET = [
    "laudo_id", "categoria_analise", "tipo_amostra", "municipio", "latitude",
    "longitude", "data_coleta", "solicitante_tipo", "tipo_resultado", "rotulo",
    "analito", "valor", "unidade", "alvo", "resultado_diagnostico", "ct", "taxon",
    "contagem", "classe", "alerta", "metodo", "confianca_extracao",
]


def exportar_dataset_pesquisa(
    conn: sqlite3.Connection,
    destino_base: str | Path,
    categoria: str | None = None,
    rotulo: str | None = None,
    gerado_em: str | None = None,
) -> int:
    """
    Exporta um dataset de pesquisa achatado (1 linha por resultado) + dicionário de dados
    + manifesto de proveniência — pronto para análise (R/Python) e depósito FAIR (DOI).

    Filtros opcionais por categoria (eixo) e/ou rótulo (analito/alvo/táxon).
    Gera: <base>.csv, <base>.dicionario.json, <base>.proveniencia.json
    """
    where, params = [], []
    if categoria:
        where.append("l.categoria_analise = ?"); params.append(categoria)
    if rotulo:
        where.append("LOWER(r.rotulo) = LOWER(?)"); params.append(rotulo)
    clausula = ("WHERE " + " AND ".join(where)) if where else ""

    linhas = conn.execute(
        f"""SELECT l.laudo_id, l.categoria_analise, l.tipo_amostra, l.municipio,
                   l.latitude, l.longitude, l.data_coleta, l.solicitante_tipo, l.confianca_geral,
                   r.tipo tipo_resultado, r.rotulo, r.analito, r.valor, r.unidade,
                   r.alvo, r.resultado_diagnostico, r.ct, r.taxon, r.contagem,
                   r.classe, r.alerta, r.metodo
            FROM resultado r JOIN laudo l ON l.id = r.laudo_fk
            {clausula}
            ORDER BY l.data_coleta, l.laudo_id""",
        params,
    ).fetchall()

    base = Path(destino_base)
    base.parent.mkdir(parents=True, exist_ok=True)

    with base.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_COLUNAS_DATASET)
        for r in linhas:
            w.writerow([
                r["laudo_id"], r["categoria_analise"], r["tipo_amostra"], r["municipio"],
                r["latitude"], r["longitude"], r["data_coleta"], r["solicitante_tipo"],
                r["tipo_resultado"], r["rotulo"], r["analito"], r["valor"], r["unidade"],
                r["alvo"], r["resultado_diagnostico"], r["ct"], r["taxon"], r["contagem"],
                r["classe"], r["alerta"], r["metodo"], r["confianca_geral"],
            ])

    base.with_name(base.stem + ".dicionario.json").write_text(
        json.dumps(DICIONARIO_DATASET, ensure_ascii=False, indent=2), encoding="utf-8")

    if gerado_em is None:
        gerado_em = datetime.datetime.now().isoformat(timespec="seconds")
    proveniencia = {
        "fonte": "CETAB Data Lake (protótipo SIPA-Bahia AI)",
        "gerado_em": gerado_em,
        "filtros": {"categoria_analise": categoria, "rotulo": rotulo},
        "n_linhas": len(linhas),
        "colunas": _COLUNAS_DATASET,
        "licenca_sugerida": "CC-BY 4.0 (definir conforme política do CETAB)",
        "observacao": "Classes/limites ILUSTRATIVOS no protótipo; trocar pelas tabelas oficiais.",
    }
    base.with_name(base.stem + ".proveniencia.json").write_text(
        json.dumps(proveniencia, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(linhas)
