"""
Sistema de Gestão de Pesquisa — projetos, editais, pesquisadores, bolsas, publicações.
Transforma o "laboratório" em "centro de pesquisa" e destrava os indicadores institucionais.

CRUD real sobre SQLite (mesmo banco do Data Lake). Roda OFFLINE.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pesquisador (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, orcid TEXT, lattes TEXT, area TEXT);
CREATE TABLE IF NOT EXISTS edital (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, agencia TEXT, ano INTEGER, valor REAL);
CREATE TABLE IF NOT EXISTS projeto (
    id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, status TEXT, financiador TEXT,
    edital_id INTEGER, inicio TEXT, fim TEXT);
CREATE TABLE IF NOT EXISTS projeto_pesquisador (
    projeto_id INTEGER, pesquisador_id INTEGER, papel TEXT);
CREATE TABLE IF NOT EXISTS bolsa (
    id INTEGER PRIMARY KEY AUTOINCREMENT, pesquisador_id INTEGER, projeto_id INTEGER,
    modalidade TEXT, valor REAL, vigencia TEXT, ativa INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS projeto_publicacao (
    projeto_id INTEGER, doi TEXT, titulo TEXT, ano INTEGER);
"""


def garantir_tabelas(conn):
    conn.executescript(ESQUEMA)


def cadastrar_pesquisador(conn, nome, orcid=None, lattes=None, area=None) -> int:
    cur = conn.execute("INSERT INTO pesquisador (nome,orcid,lattes,area) VALUES (?,?,?,?)",
                       (nome, orcid, lattes, area))
    conn.commit(); return cur.lastrowid


def cadastrar_edital(conn, nome, agencia, ano, valor) -> int:
    cur = conn.execute("INSERT INTO edital (nome,agencia,ano,valor) VALUES (?,?,?,?)",
                       (nome, agencia, ano, valor))
    conn.commit(); return cur.lastrowid


def cadastrar_projeto(conn, titulo, status, financiador, edital_id=None, inicio=None, fim=None) -> int:
    cur = conn.execute(
        "INSERT INTO projeto (titulo,status,financiador,edital_id,inicio,fim) VALUES (?,?,?,?,?,?)",
        (titulo, status, financiador, edital_id, inicio, fim))
    conn.commit(); return cur.lastrowid


def vincular_pesquisador(conn, projeto_id, pesquisador_id, papel="membro"):
    conn.execute("INSERT INTO projeto_pesquisador VALUES (?,?,?)", (projeto_id, pesquisador_id, papel))
    conn.commit()


def conceder_bolsa(conn, pesquisador_id, projeto_id, modalidade, valor, vigencia) -> int:
    cur = conn.execute(
        "INSERT INTO bolsa (pesquisador_id,projeto_id,modalidade,valor,vigencia) VALUES (?,?,?,?,?)",
        (pesquisador_id, projeto_id, modalidade, valor, vigencia))
    conn.commit(); return cur.lastrowid


def vincular_publicacao(conn, projeto_id, doi, titulo, ano):
    conn.execute("INSERT INTO projeto_publicacao VALUES (?,?,?,?)", (projeto_id, doi, titulo, ano))
    conn.commit()


def indicadores_institucionais(conn) -> dict:
    g = lambda q: conn.execute(q).fetchone()[0]
    return {
        "projetos_ativos": g("SELECT COUNT(*) FROM projeto WHERE status='ativo'"),
        "projetos_total": g("SELECT COUNT(*) FROM projeto"),
        "pesquisadores": g("SELECT COUNT(*) FROM pesquisador"),
        "bolsas_ativas": g("SELECT COUNT(*) FROM bolsa WHERE ativa=1"),
        "publicacoes": g("SELECT COUNT(*) FROM projeto_publicacao"),
        "por_financiador": dict(conn.execute(
            "SELECT financiador, COUNT(*) FROM projeto GROUP BY financiador").fetchall()),
        "investimento_editais": g("SELECT COALESCE(SUM(valor),0) FROM edital"),
    }


def exportar_indicadores(conn, destino):
    ind = indicadores_institucionais(conn)
    Path(destino).write_text(json.dumps(ind, ensure_ascii=False, indent=2), encoding="utf-8")
    return ind


def _demo():
    db = Path(__file__).parent / "saida" / "gestao_pesquisa.sqlite"
    db.parent.mkdir(exist_ok=True)
    if db.exists(): db.unlink()
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    garantir_tabelas(conn)

    p1 = cadastrar_pesquisador(conn, "Dra. Marta Souza", orcid="0000-0002-1234-5678", area="Biologia Molecular")
    p2 = cadastrar_pesquisador(conn, "Dr. Pedro Anjos", area="Entomologia")
    ed = cadastrar_edital(conn, "Universal CNPq 2026", "CNPq", 2026, 150000)
    pr = cadastrar_projeto(conn, "Epidemiologia do HLB no Recôncavo", "ativo", "CNPq", ed, "2026-01-01", "2027-12-31")
    vincular_pesquisador(conn, pr, p1, "coordenador")
    vincular_pesquisador(conn, pr, p2, "membro")
    conceder_bolsa(conn, p2, pr, "Mestrado", 2100, "2026-2028")
    vincular_publicacao(conn, pr, "10.1590/exemplo", "Dispersão do HLB em citros", 2026)
    cadastrar_projeto(conn, "Mel de cacau: caracterização", "concluido", "FAPESB")

    ind = indicadores_institucionais(conn)
    print("=== GESTÃO DE PESQUISA ===")
    for k, v in ind.items():
        print(f"  {k}: {v}")
    conn.close()
    print("Gestão de Pesquisa: OK")


if __name__ == "__main__":
    _demo()
