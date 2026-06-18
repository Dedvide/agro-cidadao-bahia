"""
LIMS — a metade da frente do ciclo: coleta da amostra → laudo oficial emitido.

Integra-se ao Data Lake existente (persistencia). Implementa:
  - cadastro de amostra com protocolo único
  - máquina de estados + CADEIA DE CUSTÓDIA (cada transição registra quem/quando)
  - vínculo amostra ↔ laudo (resultado da análise)
  - validação técnica (aprovação pelo responsável)
  - emissão do LAUDO OFICIAL (HTML print-ready) e entrega

Fluxo de status da amostra:
  cadastrada → coletada → recebida → em_analise → analisada → validada
            → laudo_emitido → entregue
"""
from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

import assinatura
from persistencia import salvar
from schema import Laudo

# transições permitidas (máquina de estados)
TRANSICOES = {
    "cadastrada": {"coletada"},
    "coletada": {"recebida"},
    "recebida": {"em_analise"},
    "em_analise": {"analisada"},
    "analisada": {"validada"},
    "validada": {"laudo_emitido"},
    "laudo_emitido": {"entregue"},
    "entregue": set(),
}


def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _proximo_seq(conn: sqlite3.Connection, tabela: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] + 1


# ───────────────────────── Cadastro e custódia ─────────────────────────

def cadastrar_amostra(conn, *, categoria_analise, tipo_amostra, municipio,
                      solicitante_nome, solicitante_tipo, coletor, data_coleta,
                      propriedade=None, ano=2026) -> tuple[int, str]:
    """Registra a amostra (status 'cadastrada') e abre a cadeia de custódia."""
    protocolo = f"CETAB-{ano}-{_proximo_seq(conn, 'amostra'):05d}"
    cur = conn.execute(
        """INSERT INTO amostra (protocolo, categoria_analise, tipo_amostra, municipio,
                propriedade, solicitante_nome, solicitante_tipo, coletor, data_coleta, status)
           VALUES (?,?,?,?,?,?,?,?,?,'cadastrada')""",
        (protocolo, categoria_analise, tipo_amostra, municipio, propriedade,
         solicitante_nome, solicitante_tipo, coletor, data_coleta),
    )
    amostra_id = cur.lastrowid
    registrar_evento(conn, amostra_id, "cadastro", coletor, f"protocolo {protocolo}")
    conn.commit()
    return amostra_id, protocolo


def registrar_evento(conn, amostra_fk, evento, responsavel, observacao=None):
    conn.execute(
        "INSERT INTO evento_custodia (amostra_fk, evento, responsavel, data, observacao) VALUES (?,?,?,?,?)",
        (amostra_fk, evento, responsavel, _agora(), observacao),
    )
    conn.commit()


def avancar_status(conn, amostra_id, novo_status, responsavel, observacao=None):
    """Valida a transição, atualiza o status e registra na cadeia de custódia."""
    atual = conn.execute("SELECT status FROM amostra WHERE id = ?", (amostra_id,)).fetchone()[0]
    if novo_status not in TRANSICOES.get(atual, set()):
        raise ValueError(f"Transição inválida: {atual} → {novo_status}")
    conn.execute("UPDATE amostra SET status = ? WHERE id = ?", (novo_status, amostra_id))
    registrar_evento(conn, amostra_id, novo_status, responsavel, observacao)
    conn.commit()


def custodia(conn, amostra_id) -> list[dict]:
    linhas = conn.execute(
        "SELECT evento, responsavel, data, observacao FROM evento_custodia WHERE amostra_fk = ? ORDER BY id",
        (amostra_id,),
    ).fetchall()
    return [dict(r) for r in linhas]


# ───────────────────────── Análise → validação → emissão ─────────────────────────

def vincular_laudo(conn, amostra_id, laudo: Laudo) -> int:
    """Salva o laudo (resultado da análise) vinculado à amostra; avança para 'analisada'."""
    laudo_pk = salvar(conn, laudo, amostra_fk=amostra_id, status="em_validacao")
    avancar_status(conn, amostra_id, "analisada", laudo.laboratorio or "laboratório",
                   "resultado lançado")
    return laudo_pk


def validar_laudo(conn, laudo_pk, responsavel) -> None:
    """Validação técnica: aprova o laudo e avança a amostra para 'validada'."""
    amostra_id = conn.execute("SELECT amostra_fk FROM laudo WHERE id = ?", (laudo_pk,)).fetchone()[0]
    conn.execute(
        "UPDATE laudo SET status = 'aprovado', validado_por = ?, data_validacao = ? WHERE id = ?",
        (responsavel, _agora(), laudo_pk),
    )
    avancar_status(conn, amostra_id, "validada", responsavel, "validação técnica")


def _conteudo_canonico(conn, laudo_pk) -> str:
    """String determinística que representa o laudo — base do hash de integridade."""
    l = conn.execute(
        """SELECT numero_laudo, categoria_analise, solicitante_nome, municipio,
                  data_emissao, validado_por, amostra_fk FROM laudo WHERE id = ?""",
        (laudo_pk,),
    ).fetchone()
    protocolo = conn.execute(
        "SELECT protocolo FROM amostra WHERE id = ?", (l["amostra_fk"],)
    ).fetchone()["protocolo"]
    resultados = conn.execute(
        "SELECT rotulo, valor_exibicao, classe FROM resultado WHERE laudo_fk = ? ORDER BY rotulo",
        (laudo_pk,),
    ).fetchall()
    partes = [l["numero_laudo"], protocolo, l["categoria_analise"], l["solicitante_nome"] or "",
              l["municipio"] or "", l["data_emissao"], l["validado_por"] or ""]
    partes += [f"{r['rotulo']}={r['valor_exibicao']}:{r['classe']}" for r in resultados]
    return "|".join(str(p) for p in partes)


def emitir_laudo(conn, laudo_pk, destino_dir: Path, ano=2026) -> tuple[str, Path]:
    """Emite o laudo oficial: número, SELO DE INTEGRIDADE + código, documento HTML, avança amostra."""
    status = conn.execute("SELECT status FROM laudo WHERE id = ?", (laudo_pk,)).fetchone()[0]
    if status != "aprovado":
        raise ValueError(f"Só emite laudo APROVADO (status atual: {status}).")
    numero = f"CETAB-LAUDO-{ano}-{_proximo_seq(conn, 'laudo WHERE numero_laudo IS NOT NULL'):05d}"
    conn.execute(
        "UPDATE laudo SET status='emitido', numero_laudo=?, data_emissao=? WHERE id=?",
        (numero, _agora(), laudo_pk),
    )
    # selo de integridade (tamper-evidence) + código de verificação
    conteudo = _conteudo_canonico(conn, laudo_pk)
    hash_laudo, codigo = assinatura.selar(conteudo)
    conn.execute(
        "UPDATE laudo SET hash_laudo=?, codigo_verificacao=? WHERE id=?",
        (hash_laudo, codigo, laudo_pk),
    )
    amostra_id = conn.execute("SELECT amostra_fk FROM laudo WHERE id=?", (laudo_pk,)).fetchone()[0]
    avancar_status(conn, amostra_id, "laudo_emitido", "sistema", f"laudo {numero} (cód. {codigo})")

    destino_dir.mkdir(parents=True, exist_ok=True)
    caminho = destino_dir / f"{numero}.html"
    caminho.write_text(_render_laudo_html(conn, laudo_pk), encoding="utf-8")
    return numero, caminho


def verificar_laudo(conn, laudo_pk) -> bool:
    """Recalcula o hash a partir do banco e confere com o selo armazenado (detecta adulteração)."""
    hash_armazenado = conn.execute(
        "SELECT hash_laudo FROM laudo WHERE id = ?", (laudo_pk,)
    ).fetchone()[0]
    if not hash_armazenado:
        return False
    return assinatura.verificar(_conteudo_canonico(conn, laudo_pk), hash_armazenado)


# ───────────────────────── Exportação para a web (painel LIMS) ─────────────────────────

def exportar_web(conn, destino_json) -> dict:
    """Exporta o estado do LIMS (amostras + custódia + laudo) como JSON para o painel web."""
    import json
    from pathlib import Path

    amostras = []
    for a in conn.execute("SELECT * FROM amostra ORDER BY id DESC").fetchall():
        laudo_row = conn.execute(
            "SELECT * FROM laudo WHERE amostra_fk = ? ORDER BY id DESC LIMIT 1", (a["id"],)
        ).fetchone()
        laudo_obj = None
        if laudo_row:
            resultados = conn.execute(
                "SELECT rotulo, valor_exibicao, classe, alerta FROM resultado WHERE laudo_fk = ?",
                (laudo_row["id"],),
            ).fetchall()
            emitido = laudo_row["status"] == "emitido"
            laudo_obj = {
                "numero": laudo_row["numero_laudo"],
                "status": laudo_row["status"],
                "validado_por": laudo_row["validado_por"],
                "data_emissao": laudo_row["data_emissao"],
                "codigo_verificacao": laudo_row["codigo_verificacao"],
                "confianca": laudo_row["confianca_geral"],
                "arquivo": f"laudos/{laudo_row['numero_laudo']}.html" if emitido else None,
                "resultados": [
                    {"rotulo": r["rotulo"], "valor": r["valor_exibicao"],
                     "classe": r["classe"], "alerta": bool(r["alerta"])}
                    for r in resultados
                ],
            }
        custodia_lista = conn.execute(
            "SELECT evento, responsavel, data, observacao FROM evento_custodia WHERE amostra_fk = ? ORDER BY id",
            (a["id"],),
        ).fetchall()
        amostras.append({
            "protocolo": a["protocolo"], "categoria_analise": a["categoria_analise"],
            "tipo_amostra": a["tipo_amostra"], "municipio": a["municipio"],
            "solicitante_nome": a["solicitante_nome"], "solicitante_tipo": a["solicitante_tipo"],
            "coletor": a["coletor"], "data_coleta": a["data_coleta"], "status": a["status"],
            "laudo": laudo_obj,
            "custodia": [dict(c) for c in custodia_lista],
        })

    por_status = {}
    for a in amostras:
        por_status[a["status"]] = por_status.get(a["status"], 0) + 1
    resumo = {
        "total": len(amostras),
        "por_status": por_status,
        "fila_validacao": sum(1 for a in amostras if a["laudo"] and a["laudo"]["status"] == "em_validacao"),
        "aguardando_emissao": sum(1 for a in amostras if a["laudo"] and a["laudo"]["status"] == "aprovado"),
        "emitidos": sum(1 for a in amostras if a["laudo"] and a["laudo"]["status"] == "emitido"),
        "entregues": por_status.get("entregue", 0),
    }
    dados = {"amostras": amostras, "resumo": resumo}
    Path(destino_json).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return dados


def entregar(conn, amostra_id, responsavel, canal="portal"):
    avancar_status(conn, amostra_id, "entregue", responsavel, f"entregue via {canal}")


# ───────────────────────── Documento oficial (HTML print-ready) ─────────────────────────

def _render_laudo_html(conn, laudo_pk) -> str:
    l = conn.execute("SELECT * FROM laudo WHERE id = ?", (laudo_pk,)).fetchone()
    prot = conn.execute(
        "SELECT protocolo, coletor, data_coleta FROM amostra WHERE id = ?", (l["amostra_fk"],)
    ).fetchone()
    resultados = conn.execute(
        "SELECT rotulo, valor_exibicao, classe, recomendacao, alerta FROM resultado WHERE laudo_fk = ?",
        (laudo_pk,),
    ).fetchall()

    linhas = ""
    for r in resultados:
        cor = "#c0392b" if r["alerta"] else "#1b7a3d"
        rec = f"<br><small><i>{r['recomendacao']}</i></small>" if r["recomendacao"] else ""
        linhas += (f"<tr><td>{r['rotulo']}</td><td>{r['valor_exibicao']}</td>"
                   f"<td style='color:{cor};font-weight:600'>{r['classe'] or '—'}{rec}</td></tr>")

    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<title>{l['numero_laudo']}</title>
<style>
  body{{font-family:Arial,sans-serif;color:#1c2530;max-width:780px;margin:24px auto;padding:0 16px}}
  .cab{{border-bottom:3px solid #1b7a3d;padding-bottom:10px;margin-bottom:16px}}
  .cab h1{{color:#1b7a3d;margin:0;font-size:20px}}
  .cab small{{color:#5a6470}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 24px;font-size:14px;margin:14px 0}}
  table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px}}
  th,td{{border:1px solid #e2e6ea;padding:7px 10px;text-align:left}}
  th{{background:#e6f3ea}}
  .assin{{margin-top:48px;border-top:1px solid #1c2530;width:300px;padding-top:6px;font-size:13px}}
  .selo{{margin-top:20px;background:#e6f3ea;border:1px solid #1b7a3d;border-radius:6px;padding:8px 10px;font-size:12px;word-break:break-all}}
  .rod{{margin-top:24px;font-size:11px;color:#5a6470;border-top:1px solid #e2e6ea;padding-top:8px}}
</style></head><body>
<div class="cab">
  <h1>CETAB — Laudo de Análise</h1>
  <small>Centro de Tecnologias Agropecuárias da Bahia · SEAGRI</small>
</div>
<div class="grid">
  <div><b>Nº do laudo:</b> {l['numero_laudo']}</div>
  <div><b>Protocolo da amostra:</b> {prot['protocolo']}</div>
  <div><b>Categoria:</b> {l['categoria_analise']}</div>
  <div><b>Tipo de amostra:</b> {l['tipo_amostra']}</div>
  <div><b>Solicitante:</b> {l['solicitante_nome'] or '—'} ({l['solicitante_tipo'] or '—'})</div>
  <div><b>Município:</b> {l['municipio'] or '—'}</div>
  <div><b>Coleta:</b> {prot['data_coleta'] or '—'} (coletor: {prot['coletor'] or '—'})</div>
  <div><b>Emissão:</b> {l['data_emissao']}</div>
</div>
<table>
  <tr><th>Parâmetro</th><th>Resultado</th><th>Interpretação / recomendação</th></tr>
  {linhas}
</table>
<div class="assin">Responsável técnico: {l['validado_por'] or '—'}<br>Validado em {l['data_validacao'] or '—'}</div>
<div class="selo">
  <b>Código de verificação:</b> {l['codigo_verificacao'] or '—'}<br>
  <small>Hash SHA-256: {l['hash_laudo'] or '—'}</small>
</div>
<div class="rod">Documento gerado pelo SIPA-Bahia AI (protótipo). Selo de INTEGRIDADE
(tamper-evidence) — não é assinatura legal; em produção, usar ICP-Brasil / gov.br.
Classificações com faixas ILUSTRATIVAS. Confiança da extração: {l['confianca_geral']}.</div>
</body></html>"""
