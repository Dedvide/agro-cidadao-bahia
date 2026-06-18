"""
Biotecnologia — produção biológica (diferente de análise: aqui se CRIA material vivo).

Cobre 4 frentes operacionais, como sistema de informação + QC + alertas:
  - micropropagação / cultura de tecidos (mudas sadias in vitro)
  - matrizes sadias / limpeza clonal (plantas-mãe livres de patógeno) → usa diagnóstico molecular
  - bioinsumos / bioprodução (biocontrole, biofertilizantes) → QC de lote
  - banco de germoplasma (conservação de acessos)

CRUD real sobre SQLite. Roda OFFLINE. Datas em AAAA-MM-DD.
(Edição gênica/CRISPR e melhoramento assistido ficam como horizonte/Fase 3.)
"""
from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cultura_tecido (
    id INTEGER PRIMARY KEY AUTOINCREMENT, lote TEXT, especie TEXT, cultivar TEXT,
    explante TEXT, meio TEXT, estagio TEXT, n_mudas INTEGER, contaminacao_pct REAL, data TEXT);
CREATE TABLE IF NOT EXISTS bioproduto (
    id INTEGER PRIMARY KEY AUTOINCREMENT, lote TEXT, microrganismo TEXT, tipo TEXT,
    concentracao_ufc TEXT, viabilidade_pct REAL, validade TEXT);
CREATE TABLE IF NOT EXISTS germoplasma (
    id INTEGER PRIMARY KEY AUTOINCREMENT, acesso TEXT, especie TEXT, origem TEXT,
    conservacao TEXT, viabilidade_pct REAL);
CREATE TABLE IF NOT EXISTS matriz_sadia (
    id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, especie TEXT,
    status_sanitario TEXT, indexada_para TEXT);
"""

# limiares de QC (ilustrativos)
CONTAMINACAO_MAX = 10.0   # % em cultura de tecidos
VIABILIDADE_MIN_BIO = 80.0
VIABILIDADE_MIN_GERM = 70.0


def garantir_tabelas(conn):
    conn.executescript(ESQUEMA)


def registrar_cultura(conn, lote, especie, cultivar, explante, meio, estagio, n_mudas, contaminacao_pct, data) -> int:
    cur = conn.execute(
        "INSERT INTO cultura_tecido (lote,especie,cultivar,explante,meio,estagio,n_mudas,contaminacao_pct,data) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (lote, especie, cultivar, explante, meio, estagio, n_mudas, contaminacao_pct, data))
    conn.commit(); return cur.lastrowid


def registrar_bioproduto(conn, lote, microrganismo, tipo, concentracao_ufc, viabilidade_pct, validade) -> int:
    cur = conn.execute(
        "INSERT INTO bioproduto (lote,microrganismo,tipo,concentracao_ufc,viabilidade_pct,validade) VALUES (?,?,?,?,?,?)",
        (lote, microrganismo, tipo, concentracao_ufc, viabilidade_pct, validade))
    conn.commit(); return cur.lastrowid


def registrar_germoplasma(conn, acesso, especie, origem, conservacao, viabilidade_pct) -> int:
    cur = conn.execute(
        "INSERT INTO germoplasma (acesso,especie,origem,conservacao,viabilidade_pct) VALUES (?,?,?,?,?)",
        (acesso, especie, origem, conservacao, viabilidade_pct))
    conn.commit(); return cur.lastrowid


def registrar_matriz(conn, codigo, especie, status_sanitario, indexada_para) -> int:
    cur = conn.execute(
        "INSERT INTO matriz_sadia (codigo,especie,status_sanitario,indexada_para) VALUES (?,?,?,?)",
        (codigo, especie, status_sanitario, indexada_para))
    conn.commit(); return cur.lastrowid


def alertas(conn, hoje: str | None = None) -> list[dict]:
    if hoje is None:
        hoje = datetime.date.today().isoformat()
    out = []
    for c in conn.execute("SELECT lote, especie, contaminacao_pct FROM cultura_tecido").fetchall():
        if c["contaminacao_pct"] is not None and c["contaminacao_pct"] > CONTAMINACAO_MAX:
            out.append({"tipo": "contaminacao_alta", "item": f"{c['lote']} ({c['especie']})",
                        "detalhe": f"{c['contaminacao_pct']}% (máx {CONTAMINACAO_MAX}%)"})
    for b in conn.execute("SELECT lote, microrganismo, viabilidade_pct, validade FROM bioproduto").fetchall():
        if b["validade"] and b["validade"] < hoje:
            out.append({"tipo": "bioproduto_vencido", "item": f"{b['microrganismo']} (lote {b['lote']})",
                        "detalhe": f"validade {b['validade']}"})
        if b["viabilidade_pct"] is not None and b["viabilidade_pct"] < VIABILIDADE_MIN_BIO:
            out.append({"tipo": "viabilidade_baixa", "item": f"{b['microrganismo']} (lote {b['lote']})",
                        "detalhe": f"{b['viabilidade_pct']}% (mín {VIABILIDADE_MIN_BIO}%)"})
    for g in conn.execute("SELECT acesso, especie, viabilidade_pct FROM germoplasma").fetchall():
        if g["viabilidade_pct"] is not None and g["viabilidade_pct"] < VIABILIDADE_MIN_GERM:
            out.append({"tipo": "germoplasma_baixa_viab", "item": f"{g['acesso']} ({g['especie']})",
                        "detalhe": f"{g['viabilidade_pct']}%"})
    for m in conn.execute("SELECT codigo, especie, status_sanitario FROM matriz_sadia").fetchall():
        if (m["status_sanitario"] or "").lower() == "infectada":
            out.append({"tipo": "matriz_infectada", "item": f"{m['codigo']} ({m['especie']})",
                        "detalhe": "descartar da rede de matrizes"})
    return out


def indicadores(conn) -> dict:
    g = lambda q: conn.execute(q).fetchone()[0]
    return {
        "mudas_em_producao": g("SELECT COALESCE(SUM(n_mudas),0) FROM cultura_tecido") or 0,
        "lotes_cultura": g("SELECT COUNT(*) FROM cultura_tecido"),
        "lotes_bioproduto": g("SELECT COUNT(*) FROM bioproduto"),
        "acessos_germoplasma": g("SELECT COUNT(*) FROM germoplasma"),
        "matrizes_sadias": g("SELECT COUNT(*) FROM matriz_sadia WHERE LOWER(status_sanitario)='sadia'"),
    }


def _demo():
    db = Path(__file__).parent / "saida" / "biotecnologia.sqlite"
    db.parent.mkdir(exist_ok=True)
    if db.exists(): db.unlink()
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    garantir_tabelas(conn)

    registrar_cultura(conn, "CT-2026-01", "Citrus sinensis", "Pera", "segmento nodal", "MS", "multiplicacao", 480, 3.0, "2026-05-01")
    registrar_cultura(conn, "CT-2026-02", "Musa spp.", "Prata-Anã", "ápice caulinar", "MS", "enraizamento", 320, 15.0, "2026-05-08")  # contaminação alta
    registrar_bioproduto(conn, "BIO-01", "Trichoderma harzianum", "biocontrole", "1e9 UFC/g", 92, "2026-12-01")
    registrar_bioproduto(conn, "BIO-02", "Bacillus subtilis", "biocontrole", "1e8 UFC/mL", 70, "2026-02-01")  # vencido + viab baixa
    registrar_germoplasma(conn, "GERM-114", "Manihot esculenta", "Recôncavo", "in vitro", 88)
    registrar_germoplasma(conn, "GERM-220", "Theobroma cacao", "Sul BA", "criopreservacao", 60)  # viab baixa
    registrar_matriz(conn, "MZ-CT-07", "Citrus sinensis", "sadia", "HLB,CVC")
    registrar_matriz(conn, "MZ-CT-09", "Citrus sinensis", "infectada", "HLB")  # descartar

    print("=== BIOTECNOLOGIA ===")
    for k, v in indicadores(conn).items():
        print(f"  {k}: {v}")
    al = alertas(conn, hoje="2026-06-04")
    print(f"  Alertas de QC: {len(al)}")
    for a in al:
        print(f"    [{a['tipo']}] {a['item']} — {a['detalhe']}")
    conn.close()
    print("Biotecnologia: OK")


if __name__ == "__main__":
    _demo()
