"""
QA/QC analítico — controle de qualidade da análise (carta de controle + regras de Westgard).

Avalia uma série de medições de uma AMOSTRA-CONTROLE (valor alvo e desvio-padrão conhecidos)
e detecta quando o método sai de controle — base do controle de qualidade laboratorial e
de acreditação (ISO/IEC 17025). Gera também a carta de Levey-Jennings.

Roda OFFLINE. matplotlib opcional (só para a figura).
"""
from __future__ import annotations

from pathlib import Path


def avaliar_controle(valores: list[float], alvo: float, desvio: float) -> dict:
    """Aplica as regras de Westgard sobre os z-scores. Retorna avaliação + violações."""
    z = [(v - alvo) / desvio for v in valores]
    viol = []

    for i, zi in enumerate(z):
        if abs(zi) > 3:
            viol.append(("1_3s", i, "ponto além de ±3 DP (rejeição)"))
    for i in range(1, len(z)):
        if abs(z[i]) > 2 and abs(z[i - 1]) > 2 and (z[i] > 0) == (z[i - 1] > 0):
            viol.append(("2_2s", i, "2 pontos consecutivos > 2 DP no mesmo lado"))
    for i in range(1, len(z)):
        if abs(z[i] - z[i - 1]) > 4:
            viol.append(("R_4s", i, "amplitude entre pontos > 4 DP"))
    for i in range(3, len(z)):
        jan = z[i - 3:i + 1]
        if all(abs(x) > 1 for x in jan) and len({x > 0 for x in jan}) == 1:
            viol.append(("4_1s", i, "4 pontos consecutivos > 1 DP no mesmo lado (alerta)"))
    for i in range(9, len(z)):
        jan = z[i - 9:i + 1]
        if len({x > 0 for x in jan}) == 1:
            viol.append(("10_x", i, "10 pontos consecutivos do mesmo lado da média (alerta)"))

    rejeicao = {"1_3s", "2_2s", "R_4s"}
    regras = {r for r, _, _ in viol}
    if regras & rejeicao:
        status = "FORA DE CONTROLE"
    elif viol:
        status = "ALERTA"
    else:
        status = "sob controle"

    return {
        "n": len(valores), "alvo": alvo, "desvio": desvio,
        "z_scores": [round(x, 2) for x in z],
        "violacoes": viol, "status": status,
    }


def gerar_carta_lj(valores, alvo, desvio, destino: Path):
    """Carta de Levey-Jennings (PNG) com linhas ±1/2/3 DP."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = list(range(1, len(valores) + 1))
    plt.figure(figsize=(7, 3.6))
    for k, cor in [(0, "#1b7a3d"), (1, "#999"), (2, "#e67e22"), (3, "#c0392b")]:
        for s in ({k, -k} if k else {0}):
            plt.axhline(alvo + s * desvio, color=cor, lw=1,
                        ls="-" if k == 0 else "--")
    cores = ["#c0392b" if abs((v - alvo) / desvio) > 2 else "#1b7a3d" for v in valores]
    plt.plot(x, valores, color="#5a6470", lw=1, zorder=1)
    plt.scatter(x, valores, c=cores, s=45, zorder=2, edgecolors="white")
    plt.title("Carta de controle (Levey-Jennings)")
    plt.xlabel("nº da medição"); plt.ylabel("valor do controle")
    plt.tight_layout()
    plt.savefig(destino, dpi=130)
    plt.close()


def _demo():
    AQUI = Path(__file__).parent
    saida = AQUI / "saida"; saida.mkdir(exist_ok=True)
    # controle alvo=100, DP=5; série com um ponto fora (118 -> z=3.6)
    valores = [101, 99, 103, 98, 102, 100, 97, 118, 101, 99]
    av = avaliar_controle(valores, alvo=100, desvio=5)
    print(f"Controle: alvo=100 DP=5 · n={av['n']} · STATUS: {av['status']}")
    print(f"  z-scores: {av['z_scores']}")
    if av["violacoes"]:
        print("  Violações de Westgard:")
        for regra, i, desc in av["violacoes"]:
            print(f"    - {regra} na medição {i+1}: {desc}")
    gerar_carta_lj(valores, 100, 5, saida / "carta_controle.png")
    print(f"  Carta gerada: saida/carta_controle.png")
    print("QA/QC analítico: OK")


if __name__ == "__main__":
    _demo()
