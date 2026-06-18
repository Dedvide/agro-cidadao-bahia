import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "interacoes.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interacoes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                data      TEXT NOT NULL,
                canal     TEXT NOT NULL,
                municipio TEXT,
                tipo      TEXT,
                pergunta  TEXT,
                resposta  TEXT
            )
        """)
        conn.commit()


def registrar(canal: str, municipio: str, pergunta: str, resposta: str, tipo: str = "texto"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO interacoes (data, canal, municipio, tipo, pergunta, resposta) VALUES (?,?,?,?,?,?)",
            (datetime.utcnow().isoformat(), canal, municipio or "", tipo, pergunta, resposta),
        )
        conn.commit()


def stats() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM interacoes").fetchone()[0]
        municipios = conn.execute(
            "SELECT COUNT(DISTINCT municipio) FROM interacoes WHERE municipio != ''"
        ).fetchone()[0]
        por_canal = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT canal, COUNT(*) FROM interacoes GROUP BY canal"
            ).fetchall()
        }
        por_tipo = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT tipo, COUNT(*) FROM interacoes GROUP BY tipo"
            ).fetchall()
        }
        recentes = conn.execute(
            "SELECT data, canal, municipio, tipo, pergunta FROM interacoes ORDER BY id DESC LIMIT 10"
        ).fetchall()

    return {
        "total_atendimentos": total,
        "municipios_alcancados": municipios,
        "por_canal": por_canal,
        "por_tipo": por_tipo,
        "ultimos_10": [
            {"data": r[0], "canal": r[1], "municipio": r[2], "tipo": r[3], "pergunta": r[4]}
            for r in recentes
        ],
    }
