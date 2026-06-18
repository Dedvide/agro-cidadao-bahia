"""
Persistência + CRUD do CRM (Camada Operacional) e as visões cruzadas que dão valor:
  - PRONTUÁRIO da propriedade (como um prontuário eletrônico): atendimentos + ocorrências
    + análises laboratoriais (puxadas do Data Lake pelo município).
  - CARTEIRA do técnico (assistência técnica): produtores/propriedades, visitas, pendências.

Banco próprio (crm.sqlite) — a Camada Operacional ALIMENTA a Analítica (Data Lake/ontologia).
Em produção: PostgreSQL (mudar só `_conn`).
"""
from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "prototipo-extrator" / "saida"
CRM_DB = SAIDA / "crm.sqlite"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS produtor (
    id INTEGER PRIMARY KEY AUTOINCREMENT, documento TEXT, nome TEXT, tipo TEXT,
    municipio TEXT, telefone TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS propriedade (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, produtor_id INTEGER,
    municipio TEXT, area_ha REAL, latitude REAL, longitude REAL, cultura_principal TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS atendimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT, propriedade_id INTEGER, tecnico TEXT, data TEXT,
    tipo TEXT, problema TEXT, orientacao TEXT, retorno_previsto TEXT, status TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS ocorrencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT, propriedade_id INTEGER, tipo TEXT, descricao TEXT,
    data TEXT, status TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def _conn() -> sqlite3.Connection:
    SAIDA.mkdir(exist_ok=True)
    c = sqlite3.connect(CRM_DB)
    c.row_factory = sqlite3.Row
    c.executescript(ESQUEMA)
    return c


def _inserir(tabela: str, dados: dict) -> dict:
    conn = _conn()
    cols = ", ".join(dados); ph = ", ".join("?" for _ in dados)
    cur = conn.execute(f"INSERT INTO {tabela} ({cols}) VALUES ({ph})", tuple(dados.values()))
    novo = dict(conn.execute(f"SELECT * FROM {tabela} WHERE id=?", (cur.lastrowid,)).fetchone())
    conn.commit(); conn.close()
    return novo


def _listar(tabela: str, where: str = "", params=()) -> list[dict]:
    conn = _conn()
    rows = conn.execute(f"SELECT * FROM {tabela} {where} ORDER BY id DESC", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ───────────────────────── CRUD ─────────────────────────

def cadastrar_produtor(d: dict) -> dict: return _inserir("produtor", d)
def listar_produtores() -> list[dict]: return _listar("produtor")
def cadastrar_propriedade(d: dict) -> dict: return _inserir("propriedade", d)
def listar_propriedades() -> list[dict]: return _listar("propriedade")
def registrar_atendimento(d: dict) -> dict: return _inserir("atendimento", d)
def listar_atendimentos() -> list[dict]: return _listar("atendimento")
def abrir_ocorrencia(d: dict) -> dict: return _inserir("ocorrencia", d)


# ───────────────────────── Visões cruzadas (o valor) ─────────────────────────

def _analises_do_municipio(municipio: str) -> list[dict]:
    """Puxa análises do Data Lake pelo município (liga Operacional ↔ Analítica)."""
    if not municipio:
        return []
    import servico
    try:
        conn = sqlite3.connect(servico._db()); conn.row_factory = sqlite3.Row
    except Exception:
        return []
    rows = conn.execute(
        """SELECT laudo_id, categoria_analise, data_coleta FROM laudo
           WHERE LOWER(municipio)=LOWER(?) ORDER BY data_coleta DESC LIMIT 20""",
        (municipio,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def prontuario_propriedade(prop_id: int) -> dict | None:
    """Prontuário eletrônico da propriedade: histórico completo num lugar só."""
    conn = _conn()
    prop = conn.execute("SELECT * FROM propriedade WHERE id=?", (prop_id,)).fetchone()
    if not prop:
        conn.close(); return None
    prod = conn.execute("SELECT nome, documento, tipo FROM produtor WHERE id=?",
                        (prop["produtor_id"],)).fetchone()
    atend = conn.execute("SELECT * FROM atendimento WHERE propriedade_id=? ORDER BY data DESC",
                         (prop_id,)).fetchall()
    ocor = conn.execute("SELECT * FROM ocorrencia WHERE propriedade_id=? ORDER BY data DESC",
                        (prop_id,)).fetchall()
    conn.close()
    return {
        "propriedade": dict(prop),
        "produtor": dict(prod) if prod else None,
        "atendimentos": [dict(a) for a in atend],
        "ocorrencias": [dict(o) for o in ocor],
        "analises_laboratoriais": _analises_do_municipio(prop["municipio"]),
    }


def carteira_tecnico(tecnico: str) -> dict:
    """Carteira digital de produtores do técnico (assistência técnica)."""
    conn = _conn()
    atend = conn.execute("SELECT * FROM atendimento WHERE LOWER(tecnico)=LOWER(?)",
                         (tecnico,)).fetchall()
    props = {a["propriedade_id"] for a in atend}
    municipios = set()
    for pid in props:
        r = conn.execute("SELECT municipio FROM propriedade WHERE id=?", (pid,)).fetchone()
        if r and r["municipio"]:
            municipios.add(r["municipio"])
    pendencias = [dict(a) for a in atend if (a["status"] or "") != "concluido"]
    conn.close()
    return {
        "tecnico": tecnico,
        "propriedades_atendidas": len(props),
        "municipios": sorted(municipios),
        "visitas_realizadas": len(atend),
        "pendencias": len(pendencias),
        "proximos_retornos": sorted(
            [{"propriedade_id": a["propriedade_id"], "retorno_previsto": a["retorno_previsto"],
              "problema": a["problema"]} for a in pendencias if a["retorno_previsto"]],
            key=lambda x: x["retorno_previsto"])[:10],
    }
