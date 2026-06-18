"""
Repositório Científico + busca (RAG real, sem API).

Armazena documentos (artigos, teses, protocolos, datasets) e implementa recuperação
por relevância com TF-IDF + cosseno — em Python puro, sem dependências externas.
É a base de recuperação do RAG: substitui o stub por palavra-chave do rag_cientifico.

Em produção: trocar TF-IDF por embeddings + pgvector/Qdrant (busca semântica).
"""
from __future__ import annotations

import math
import re
import sqlite3
from collections import Counter
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS documento (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, titulo TEXT, autores TEXT,
    doi TEXT, ano INTEGER, caminho TEXT, texto TEXT);
"""
_STOP = set("a o as os de da do das dos e em no na nos nas para com por que um uma "
            "the of and to in for on is are with".split())


def garantir_tabelas(conn):
    conn.executescript(ESQUEMA)


def registrar_documento(conn, tipo, titulo, texto, autores=None, doi=None, ano=None, caminho=None) -> int:
    cur = conn.execute(
        "INSERT INTO documento (tipo,titulo,autores,doi,ano,caminho,texto) VALUES (?,?,?,?,?,?,?)",
        (tipo, titulo, autores, doi, ano, caminho, texto))
    conn.commit(); return cur.lastrowid


def _tokens(texto: str) -> list[str]:
    return [t for t in re.findall(r"\w+", (texto or "").lower()) if len(t) > 2 and t not in _STOP]


def _tfidf(docs_tokens: list[list[str]]) -> tuple[list[dict], dict]:
    n = len(docs_tokens)
    df = Counter()
    for toks in docs_tokens:
        df.update(set(toks))
    idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in df}
    vetores = []
    for toks in docs_tokens:
        tf = Counter(toks)
        total = len(toks) or 1
        vetores.append({t: (c / total) * idf[t] for t, c in tf.items()})
    return vetores, idf


def _cos(a: dict, b: dict) -> float:
    comum = set(a) & set(b)
    num = sum(a[t] * b[t] for t in comum)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return num / (na * nb) if na and nb else 0.0


def buscar(conn, consulta: str, k: int = 3) -> list[dict]:
    """Recupera os k documentos mais relevantes para a consulta (TF-IDF + cosseno)."""
    docs = conn.execute("SELECT id,tipo,titulo,autores,doi,ano,texto FROM documento").fetchall()
    if not docs:
        return []
    corpus_tokens = [_tokens(d["titulo"] + " " + (d["texto"] or "")) for d in docs]
    vetores, idf = _tfidf(corpus_tokens)
    q_toks = _tokens(consulta)
    tfq = Counter(q_toks); total = len(q_toks) or 1
    qv = {t: (c / total) * idf.get(t, 0.0) for t, c in tfq.items()}
    ranqueados = sorted(
        ({"doc": dict(d), "score": _cos(qv, v)} for d, v in zip(docs, vetores)),
        key=lambda x: x["score"], reverse=True)
    return [r for r in ranqueados if r["score"] > 0][:k]


def _demo():
    db = Path(__file__).parent / "saida" / "repositorio.sqlite"
    db.parent.mkdir(exist_ok=True)
    if db.exists(): db.unlink()
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    garantir_tabelas(conn)

    registrar_documento(conn, "artigo", "Resistência da mangueira à antracnose (Colletotrichum)",
        "Estudo avaliou genótipos de manga quanto à resistência à antracnose causada por "
        "Colletotrichum gloeosporioides em condições de alta umidade no semiárido.", doi="10.x/manga", ano=2024)
    registrar_documento(conn, "tese", "Epidemiologia do HLB em citros no Recôncavo Baiano",
        "Dispersão espacial do greening dos citros e do psilídeo vetor em pomares da Bahia.", ano=2025)
    registrar_documento(conn, "protocolo", "Detecção molecular de Xylella fastidiosa por qPCR",
        "Protocolo de extração e qPCR para diagnóstico de CVC em citros.", ano=2023)

    consulta = "resistência da manga à antracnose"
    print("=== REPOSITÓRIO + RAG (TF-IDF) ===")
    print(f"  Consulta: \"{consulta}\"")
    for r in buscar(conn, consulta, k=3):
        print(f"    {r['score']:.3f}  {r['doc']['titulo']} ({r['doc'].get('ano')})")
    conn.close()
    print("Repositório + RAG real: OK")


if __name__ == "__main__":
    _demo()
