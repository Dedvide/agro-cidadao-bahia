"""
Camada de persistência — o Data Lake Agropecuário (protótipo), multi-eixo.

Protótipo: SQLite (zero setup). Produção: PostgreSQL + PostGIS (mesma estrutura;
latitude/longitude viram geometria).

Grava o Laudo + cada resultado JÁ INTERPRETADO (rótulo, exibição, classe, alerta),
georreferenciando pelo município quando não há coordenada.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from interpretar import interpretar_resultado
from municipios_ba import centroide
from schema import Laudo

ESQUEMA = """
CREATE TABLE IF NOT EXISTS amostra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo TEXT UNIQUE,
    categoria_analise TEXT,
    tipo_amostra TEXT,
    municipio TEXT,
    propriedade TEXT,
    latitude REAL,
    longitude REAL,
    solicitante_nome TEXT,
    solicitante_tipo TEXT,
    coletor TEXT,
    data_coleta TEXT,
    status TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evento_custodia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amostra_fk INTEGER REFERENCES amostra(id),
    evento TEXT,
    responsavel TEXT,
    data TEXT DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT
);

CREATE TABLE IF NOT EXISTS laudo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    laudo_id TEXT,
    amostra_fk INTEGER REFERENCES amostra(id),
    numero_laudo TEXT,
    status TEXT DEFAULT 'rascunho',
    validado_por TEXT,
    data_validacao TEXT,
    data_emissao TEXT,
    hash_laudo TEXT,
    codigo_verificacao TEXT,
    categoria_analise TEXT,
    tipo_amostra TEXT,
    data_coleta TEXT,
    data_analise TEXT,
    solicitante_nome TEXT,
    solicitante_tipo TEXT,
    municipio TEXT,
    propriedade TEXT,
    latitude REAL,
    longitude REAL,
    laboratorio TEXT,
    confianca_geral REAL,
    campos_incertos TEXT,
    observacoes_extracao TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    laudo_fk INTEGER REFERENCES laudo(id),
    tipo TEXT,
    -- campos brutos
    analito TEXT, valor REAL, valor_texto TEXT, unidade TEXT,
    alvo TEXT, resultado_diagnostico TEXT, ct REAL,
    taxon TEXT, contagem INTEGER, estagio TEXT,
    metodo TEXT,
    -- interpretação computada
    rotulo TEXT, valor_exibicao TEXT, classe TEXT,
    detalhe TEXT, recomendacao TEXT, alerta INTEGER
);
"""


def conectar(caminho: str | Path = "datalake.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(str(caminho))
    conn.row_factory = sqlite3.Row
    conn.executescript(ESQUEMA)
    return conn


def salvar(conn: sqlite3.Connection, laudo: Laudo,
           amostra_fk: int | None = None, status: str = "rascunho") -> int:
    """Persiste um Laudo + resultados interpretados. Retorna o id. Georreferencia.
    Opcionalmente vincula a uma amostra (LIMS) e define o status do laudo."""
    lat, lon = laudo.latitude, laudo.longitude
    if lat is None or lon is None:
        lat, lon = centroide(laudo.municipio)

    cur = conn.execute(
        """INSERT INTO laudo (laudo_id, amostra_fk, status, categoria_analise, tipo_amostra,
                data_coleta, data_analise, solicitante_nome, solicitante_tipo, municipio,
                propriedade, latitude, longitude, laboratorio, confianca_geral,
                campos_incertos, observacoes_extracao)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            laudo.laudo_id, amostra_fk, status, laudo.categoria_analise,
            laudo.tipo_amostra.value, laudo.data_coleta, laudo.data_analise,
            laudo.solicitante_nome,
            laudo.solicitante_tipo.value if laudo.solicitante_tipo else None,
            laudo.municipio, laudo.propriedade, lat, lon, laudo.laboratorio,
            laudo.confianca_geral,
            json.dumps(laudo.campos_incertos, ensure_ascii=False),
            laudo.observacoes_extracao,
        ),
    )
    laudo_fk = cur.lastrowid

    for r in laudo.resultados:
        it = interpretar_resultado(laudo.categoria_analise, r)
        conn.execute(
            """INSERT INTO resultado (laudo_fk, tipo, analito, valor, valor_texto, unidade,
                    alvo, resultado_diagnostico, ct, taxon, contagem, estagio, metodo,
                    rotulo, valor_exibicao, classe, detalhe, recomendacao, alerta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                laudo_fk, r.tipo.value, r.analito, r.valor, r.valor_texto, r.unidade,
                r.alvo, r.resultado_diagnostico, r.ct, r.taxon, r.contagem, r.estagio, r.metodo,
                it.rotulo, it.valor_exibicao, it.classe, it.detalhe, it.recomendacao,
                1 if it.alerta else 0,
            ),
        )
    conn.commit()
    return laudo_fk
