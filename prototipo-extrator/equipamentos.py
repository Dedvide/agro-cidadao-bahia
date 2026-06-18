"""
Gestão de Equipamentos e Reagentes (completa o LIMS).
- Equipamentos: calibração (vencida → bloqueia uso).
- Reagentes: lote, validade, estoque mínimo (vencido / baixo → alerta).

CRUD real sobre SQLite. Roda OFFLINE. Datas em AAAA-MM-DD.
"""
from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS equipamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, modelo TEXT, fabricante TEXT,
    ultima_calibracao TEXT, proxima_calibracao TEXT, status TEXT DEFAULT 'ativo');
CREATE TABLE IF NOT EXISTS reagente (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, lote TEXT, validade TEXT,
    estoque REAL, unidade TEXT, minimo REAL);
"""


def garantir_tabelas(conn):
    conn.executescript(ESQUEMA)


def cadastrar_equipamento(conn, nome, modelo, fabricante, ultima_calibracao, proxima_calibracao) -> int:
    cur = conn.execute(
        "INSERT INTO equipamento (nome,modelo,fabricante,ultima_calibracao,proxima_calibracao) VALUES (?,?,?,?,?)",
        (nome, modelo, fabricante, ultima_calibracao, proxima_calibracao))
    conn.commit(); return cur.lastrowid


def cadastrar_reagente(conn, nome, lote, validade, estoque, unidade, minimo) -> int:
    cur = conn.execute(
        "INSERT INTO reagente (nome,lote,validade,estoque,unidade,minimo) VALUES (?,?,?,?,?,?)",
        (nome, lote, validade, estoque, unidade, minimo))
    conn.commit(); return cur.lastrowid


def alertas(conn, hoje: str | None = None) -> list[dict]:
    """Lista pendências: calibração vencida, reagente vencido, estoque baixo."""
    if hoje is None:
        hoje = datetime.date.today().isoformat()
    out = []
    for e in conn.execute("SELECT nome, proxima_calibracao FROM equipamento").fetchall():
        if e["proxima_calibracao"] and e["proxima_calibracao"] < hoje:
            out.append({"tipo": "calibracao_vencida", "item": e["nome"],
                        "detalhe": f"vencida em {e['proxima_calibracao']}"})
    for r in conn.execute("SELECT nome, lote, validade, estoque, minimo, unidade FROM reagente").fetchall():
        if r["validade"] and r["validade"] < hoje:
            out.append({"tipo": "reagente_vencido", "item": f"{r['nome']} (lote {r['lote']})",
                        "detalhe": f"validade {r['validade']}"})
        if r["estoque"] is not None and r["minimo"] is not None and r["estoque"] < r["minimo"]:
            out.append({"tipo": "estoque_baixo", "item": r["nome"],
                        "detalhe": f"{r['estoque']} {r['unidade']} (mín. {r['minimo']})"})
    return out


def _demo():
    db = Path(__file__).parent / "saida" / "equipamentos.sqlite"
    db.parent.mkdir(exist_ok=True)
    if db.exists(): db.unlink()
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    garantir_tabelas(conn)

    cadastrar_equipamento(conn, "Termociclador qPCR", "CFX96", "Bio-Rad", "2025-06-01", "2026-06-01")
    cadastrar_equipamento(conn, "Espectrômetro AA", "AA-7000", "Shimadzu", "2025-01-10", "2025-12-10")  # vencida
    cadastrar_reagente(conn, "Taq DNA Polimerase", "L2024A", "2026-12-31", 40, "U", 10)
    cadastrar_reagente(conn, "Master Mix qPCR", "L2023X", "2026-01-15", 5, "mL", 10)  # vencido + baixo

    al = alertas(conn, hoje="2026-06-04")
    print("=== EQUIPAMENTOS & REAGENTES ===")
    print(f"  Pendências: {len(al)}")
    for a in al:
        print(f"    [{a['tipo']}] {a['item']} — {a['detalhe']}")
    conn.close()
    print("Equipamentos & Reagentes: OK")


if __name__ == "__main__":
    _demo()
