"""
Núcleo Científico (A) — RAG Científico híbrido (ESBOÇO wired).

Roteia a pergunta entre DUAS fontes e sempre cita:
  • dado numérico/série  → Text-to-SQL (read-only) sobre o Data Lake  → resposta EXATA
  • conhecimento/contexto → recuperação no corpus de publicações       → resposta + DOI

Estado: esqueleto. O caminho Text-to-SQL roda com ANTHROPIC_API_KEY; a recuperação
vetorial está como stub por palavra-chave (trocar por pgvector/Qdrant na Fase 3).

Uso:  python rag_cientifico.py "qual a média de fósforo em Cruz das Almas?"
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

AQUI = Path(__file__).parent
DB_PADRAO = AQUI.parent / "prototipo-extrator" / "saida" / "datalake_painel.sqlite"
CORPUS = AQUI / "publicacoes_seed.json"
MODELO = os.environ.get("CETAB_MODELO", "claude-sonnet-4-6")

# Esquema do Data Lake exposto ao LLM para o Text-to-SQL.
ESQUEMA_BANCO = """
Tabelas (SQLite):
laudo(id, laudo_id, categoria_analise, tipo_amostra, data_coleta, municipio,
      solicitante_tipo, latitude, longitude, confianca_geral)
resultado(laudo_fk -> laudo.id, tipo, analito, valor, unidade, alvo,
          resultado_diagnostico, ct, taxon, contagem, classe, alerta, rotulo)
Notas: 'rotulo' = analito/alvo/taxon padronizado; 'alerta'=1 quando fora do ideal;
categoria_analise ex.: fertilidade_solo, diagnostico_molecular, monitoramento_pragas.
"""

SOMENTE_SELECT = re.compile(r"^\s*select\b", re.IGNORECASE)
PROIBIDO = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", re.IGNORECASE)


def _validar_sql(sql: str) -> bool:
    return bool(SOMENTE_SELECT.match(sql)) and not PROIBIDO.search(sql)


def _roteador(pergunta: str) -> str:
    """Heurística simples: números/agregações → dados; senão → literatura."""
    chaves_dado = ("média", "media", "quantos", "quantas", "total", "taxa",
                   "positiv", "contagem", "máx", "min", "por município", "série")
    return "dados" if any(k in pergunta.lower() for k in chaves_dado) else "literatura"


# ─────────── (1) Caminho DADOS: Text-to-SQL read-only ───────────

def responder_dados(pergunta: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    tool = {
        "name": "consultar_sql",
        "description": "Gera UMA consulta SQL SELECT (read-only) para responder a pergunta.",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "Apenas SELECT."}},
            "required": ["sql"],
        },
    }
    resp = client.messages.create(
        model=MODELO, max_tokens=600,
        system=[{"type": "text", "text": "Você gera SQL SELECT para SQLite.\n" + ESQUEMA_BANCO,
                 "cache_control": {"type": "ephemeral"}}],
        tools=[tool], tool_choice={"type": "tool", "name": "consultar_sql"},
        messages=[{"role": "user", "content": pergunta}],
    )
    sql = next(b.input["sql"] for b in resp.content if b.type == "tool_use")
    if not _validar_sql(sql):
        return f"[bloqueado] consulta não é read-only:\n{sql}"
    conn = sqlite3.connect(DB_PADRAO)
    try:
        linhas = conn.execute(sql).fetchall()
    finally:
        conn.close()
    return f"Resposta (fonte: Data Lake)\nSQL: {sql}\nResultado: {linhas}"


# ─────────── (2) Caminho LITERATURA: recuperação no corpus (stub) ───────────

def responder_literatura(pergunta: str) -> str:
    pubs = json.loads(CORPUS.read_text(encoding="utf-8"))["publicacoes"]
    termos = [t for t in re.findall(r"\w+", pergunta.lower()) if len(t) > 3]
    ranqueadas = sorted(
        pubs, key=lambda p: sum(t in p["titulo"].lower() for t in termos), reverse=True
    )
    top = [p for p in ranqueadas if any(t in p["titulo"].lower() for t in termos)][:3]
    if not top:
        return "Não encontrei publicação relacionada no corpus (stub por palavra-chave)."
    linhas = [f"- {p['titulo']} ({p['ano']}) — DOI {p['doi']}" for p in top]
    return "Publicações relacionadas (fonte: corpus):\n" + "\n".join(linhas) + \
        "\n[stub: trocar por busca vetorial + síntese LLM com citação na Fase 3]"


def responder(pergunta: str) -> str:
    if _roteador(pergunta) == "dados":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return "[Text-to-SQL precisa de ANTHROPIC_API_KEY]"
        return responder_dados(pergunta)
    return responder_literatura(pergunta)


def main(argv) -> int:
    if not argv:
        print('Uso: python rag_cientifico.py "sua pergunta"')
        return 2
    print(responder(" ".join(argv)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
