"""
Núcleo Científico (B) — Gerador de relatório/figuras para artigos.

Lê o dataset de pesquisa exportado pelo Data Lake e produz:
  - figuras publicáveis (PNG) em figuras/
  - um rascunho de relatório (relatorio.md) com descrição dos dados,
    parágrafo de métodos, estatística descritiva e figuras embutidas.

Roda OFFLINE (sem API). Só matplotlib.

Uso:  python gerar_relatorio.py [caminho_do_dataset.csv]
Padrão: ../prototipo-extrator/saida/dataset_pesquisa.csv
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sem tela
import matplotlib.pyplot as plt

AQUI = Path(__file__).parent
DATASET_PADRAO = AQUI.parent / "prototipo-extrator" / "saida" / "dataset_pesquisa.csv"
FIGURAS = AQUI / "figuras"
VERDE, VERMELHO, CINZA = "#1b7a3d", "#c0392b", "#5a6470"


def carregar(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fig_laudos_por_mes(linhas, destino):
    meses = sorted({r["data_coleta"][:7] for r in linhas if r["data_coleta"]})
    laudos_por_mes = {m: set() for m in meses}
    for r in linhas:
        if r["data_coleta"]:
            laudos_por_mes[r["data_coleta"][:7]].add(r["laudo_id"])
    valores = [len(laudos_por_mes[m]) for m in meses]
    plt.figure(figsize=(6, 3.2))
    plt.bar(meses, valores, color=VERDE)
    plt.title("Laudos por mês")
    plt.ylabel("nº de laudos")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(destino, dpi=130)
    plt.close()


def fig_taxa_alerta_por_eixo(linhas, destino):
    total = defaultdict(set)
    alerta = defaultdict(set)
    for r in linhas:
        cat = r["categoria_analise"]
        total[cat].add(r["laudo_id"])
        if r["alerta"] == "1":
            alerta[cat].add(r["laudo_id"])
    cats = sorted(total, key=lambda c: -len(total[c]))
    taxa = [100 * len(alerta[c]) / len(total[c]) for c in cats]
    plt.figure(figsize=(6, 3.2))
    plt.barh(cats, taxa, color=VERMELHO)
    plt.title("Taxa de alerta por eixo (%)")
    plt.xlabel("% de laudos com alerta")
    plt.tight_layout()
    plt.savefig(destino, dpi=130)
    plt.close()


def fig_distribuicao(linhas, analito, destino):
    classes = Counter(r["classe"] for r in linhas
                      if r["rotulo"].lower() == analito and r["classe"])
    if not classes:
        return False
    rotulos, valores = zip(*classes.most_common())
    plt.figure(figsize=(5, 3.2))
    plt.bar(rotulos, valores, color=VERDE)
    plt.title(f"Distribuição de classes — {analito}")
    plt.ylabel("nº de amostras")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(destino, dpi=130)
    plt.close()
    return True


def fig_dispersao_geografica(linhas, destino):
    pontos = {}
    for r in linhas:
        if r["latitude"] and r["longitude"]:
            alerta = pontos.get(r["laudo_id"], (0,))[0] or (r["alerta"] == "1")
            pontos[r["laudo_id"]] = (alerta, float(r["latitude"]), float(r["longitude"]))
    plt.figure(figsize=(5, 4.2))
    for alerta, lat, lon in pontos.values():
        plt.scatter(lon, lat, c=VERMELHO if alerta else VERDE, s=60,
                    edgecolors="white", linewidths=1)
    plt.title("Dispersão geográfica das amostras")
    plt.xlabel("longitude"); plt.ylabel("latitude")
    plt.tight_layout()
    plt.savefig(destino, dpi=130)
    plt.close()


def estatistica_descritiva(linhas):
    """Média/mín/máx por (eixo, analito) quantitativo."""
    grupos = defaultdict(list)
    for r in linhas:
        if r["tipo_resultado"] == "quantitativo" and r["valor"]:
            grupos[(r["categoria_analise"], r["rotulo"])].append(float(r["valor"]))
    tabela = []
    for (cat, analito), vals in sorted(grupos.items()):
        tabela.append((cat, analito, len(vals), round(statistics.mean(vals), 2),
                       min(vals), max(vals)))
    return tabela


def gerar_relatorio(caminho: Path):
    linhas = carregar(caminho)
    FIGURAS.mkdir(exist_ok=True)

    fig_laudos_por_mes(linhas, FIGURAS / "laudos_por_mes.png")
    fig_taxa_alerta_por_eixo(linhas, FIGURAS / "taxa_alerta_por_eixo.png")
    tem_fosforo = fig_distribuicao(linhas, "fosforo", FIGURAS / "distribuicao_fosforo.png")
    fig_dispersao_geografica(linhas, FIGURAS / "dispersao_geografica.png")

    laudos = {r["laudo_id"] for r in linhas}
    eixos = sorted({r["categoria_analise"] for r in linhas})
    datas = sorted(r["data_coleta"] for r in linhas if r["data_coleta"])
    periodo = f"{datas[0]} a {datas[-1]}" if datas else "—"

    tab = estatistica_descritiva(linhas)
    tab_md = "| Eixo | Parâmetro | n | média | mín | máx |\n|---|---|---|---|---|---|\n"
    tab_md += "\n".join(f"| {c} | {a} | {n} | {m} | {mi} | {ma} |" for c, a, n, m, mi, ma in tab)

    md = f"""# Relatório automático — CETAB / SIPA-Bahia AI

> Rascunho gerado pelo Núcleo Científico a partir do Data Lake.
> Revisar e validar antes de qualquer publicação. Números provêm dos dados; texto é sugestão.

## Descrição dos dados
- **Registros (resultados):** {len(linhas)}
- **Laudos:** {len(laudos)}
- **Eixos de análise:** {", ".join(eixos)}
- **Período de coleta:** {periodo}

## Material e Métodos (rascunho)
As amostras foram analisadas nos laboratórios do CETAB e os resultados normalizados por
extração assistida por IA para um esquema canônico, com classificação automática contra
faixas de referência e revisão humana dos casos de baixa confiança. Os dados foram
consolidados em um Data Lake georreferenciado, do qual este conjunto foi extraído com
proveniência registrada.

## Estatística descritiva
{tab_md}

## Figuras
![Laudos por mês](figuras/laudos_por_mes.png)

![Taxa de alerta por eixo](figuras/taxa_alerta_por_eixo.png)
{"![Distribuição de fósforo](figuras/distribuicao_fosforo.png)" if tem_fosforo else ""}

![Dispersão geográfica](figuras/dispersao_geografica.png)
"""
    (AQUI / "relatorio.md").write_text(md, encoding="utf-8")
    print(f"Relatório gerado: relatorio.md")
    print(f"Figuras em figuras/: {len(list(FIGURAS.glob('*.png')))} arquivo(s)")
    print(f"  {len(linhas)} resultados · {len(laudos)} laudos · {len(eixos)} eixos · período {periodo}")


def main(argv):
    caminho = Path(argv[0]) if argv else DATASET_PADRAO
    if not caminho.exists():
        print(f"Dataset não encontrado: {caminho}\n"
              f"Rode antes: cd ../prototipo-extrator ; python gerar_painel_demo.py")
        return 1
    gerar_relatorio(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
