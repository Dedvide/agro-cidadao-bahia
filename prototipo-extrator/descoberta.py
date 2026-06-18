"""
IA Científica — descoberta de padrões e geração de hipóteses sobre o Data Lake.

Sem LLM: estatística aplicada (Pearson entre analitos, associação município→alerta)
para sugerir HIPÓTESES que o pesquisador investiga. A IA aponta, o humano valida.

Roda OFFLINE.
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from pathlib import Path


def _pearson(xs, ys) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (dx * dy) if dx and dy else 0.0


def correlacoes_analitos(conn, categoria: str, limiar: float = 0.5) -> list[dict]:
    """Pearson entre pares de analitos quantitativos dentro de uma categoria."""
    linhas = conn.execute(
        """SELECT l.id laudo, r.analito, r.valor FROM resultado r JOIN laudo l ON l.id=r.laudo_fk
           WHERE l.categoria_analise=? AND r.tipo='quantitativo' AND r.valor IS NOT NULL""",
        (categoria,)).fetchall()
    por_laudo = defaultdict(dict)
    for x in linhas:
        por_laudo[x["laudo"]][x["analito"]] = x["valor"]
    analitos = sorted({x["analito"] for x in linhas})
    out = []
    for i in range(len(analitos)):
        for j in range(i + 1, len(analitos)):
            a, b = analitos[i], analitos[j]
            pares = [(d[a], d[b]) for d in por_laudo.values() if a in d and b in d]
            if len(pares) >= 3:
                r = _pearson([p[0] for p in pares], [p[1] for p in pares])
                if abs(r) >= limiar:
                    out.append({"a": a, "b": b, "r": round(r, 2), "n": len(pares)})
    return sorted(out, key=lambda d: -abs(d["r"]))


def associacao_municipio_alerta(conn) -> list[dict]:
    linhas = conn.execute(
        """SELECT l.municipio mun, COUNT(DISTINCT l.id) n,
                  COUNT(DISTINCT CASE WHEN r.alerta=1 THEN l.id END) alertas
           FROM laudo l LEFT JOIN resultado r ON r.laudo_fk=l.id
           WHERE l.municipio IS NOT NULL GROUP BY l.municipio HAVING n>=2""").fetchall()
    return sorted(
        [{"municipio": x["mun"], "taxa_alerta": round(x["alertas"]/x["n"], 2), "n": x["n"]}
         for x in linhas], key=lambda d: -d["taxa_alerta"])


def gerar_hipoteses(conn) -> list[str]:
    hip = []
    for c in correlacoes_analitos(conn, "fertilidade_solo"):
        sentido = "positiva" if c["r"] > 0 else "negativa"
        hip.append(f"Há correlação {sentido} (r={c['r']}, n={c['n']}) entre {c['a']} e {c['b']} "
                   f"no solo — investigar relação causal.")
    altas = [m for m in associacao_municipio_alerta(conn) if m["taxa_alerta"] >= 0.5]
    for m in altas[:3]:
        hip.append(f"{m['municipio']} concentra alta taxa de alerta ({int(m['taxa_alerta']*100)}%, "
                   f"n={m['n']}) — possível foco a priorizar.")
    return hip or ["Sem padrão forte com os dados atuais (amostra pequena)."]


def _demo():
    # banco do painel (gerado por gerar_painel_demo) ou cria um sintético com correlação
    db = Path(__file__).parent / "saida" / "datalake_painel.sqlite"
    if not db.exists():
        print("(rode gerar_painel_demo.py antes para popular o Data Lake)")
        return
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    print("=== DESCOBERTA DE PADRÕES / HIPÓTESES ===")
    print("  Correlações no solo:")
    for c in correlacoes_analitos(conn, "fertilidade_solo", limiar=0.3):
        print(f"    {c['a']} ~ {c['b']}: r={c['r']} (n={c['n']})")
    print("  Hipóteses geradas:")
    for h in gerar_hipoteses(conn):
        print(f"    - {h}")
    conn.close()
    print("Descoberta de padrões: OK")


if __name__ == "__main__":
    _demo()
