"""
Referências para INTERPRETAÇÃO automática — todos os 5 eixos do CETAB.

ATENÇÃO — VALORES ILUSTRATIVOS PARA O PROTÓTIPO.
Em produção, substituir por:
  - tabelas oficiais CETAB/Embrapa (fertilidade, foliar) por método e cultura;
  - LMR oficiais (ANVISA/MAPA) para resíduos e metais;
  - níveis de ação (MIP) oficiais para pragas;
  - protocolos de diagnóstico molecular validados.
A engrenagem de classificação é a mesma; só os números mudam.

Formato das faixas: lista de (limite_inferior, limite_superior, classe), intervalo [inf, sup).
"""

INF = 1e12

# ───────────────────────── QUANTITATIVO: faixas por categoria × analito ─────────────────────────
FAIXAS = {
    "fertilidade_solo": {
        "ph": [(0, 5.0, "muito baixo (acido)"), (5.0, 5.5, "baixo"),
               (5.5, 6.5, "adequado"), (6.5, 14, "alto")],
        "fosforo": [(0, 10, "baixo"), (10, 20, "medio"), (20, INF, "alto")],
        "potassio": [(0, 40, "baixo"), (40, 80, "medio"), (80, INF, "alto")],
        "materia_organica": [(0, 1.5, "baixo"), (1.5, 3.0, "medio"), (3.0, INF, "alto")],
    },
    "analise_agua": {
        "ph": [(0, 6.0, "fora do padrao"), (6.0, 9.0, "conforme"), (9.0, 14, "fora do padrao")],
        "turbidez": [(0, 5, "conforme"), (5, INF, "acima do limite")],  # UNT (ilustrativo)
        "coliformes_termotolerantes": [(0, 1, "conforme"), (1, INF, "acima do limite")],
    },
    "analise_foliar": {
        "nitrogenio": [(0, 25, "baixo"), (25, 35, "adequado"), (35, INF, "alto")],  # g/kg ilustrativo
        "fosforo": [(0, 1.5, "baixo"), (1.5, 3.0, "adequado"), (3.0, INF, "alto")],
    },
    "qualidade_alimentos": {
        # Mel: ilustrativo (faixas inspiradas em parâmetros de qualidade).
        "umidade": [(0, 20, "conforme"), (20, INF, "acima do limite")],
        "hmf": [(0, 60, "conforme"), (60, INF, "acima do limite")],  # mg/kg
        "acidez": [(0, 50, "conforme"), (50, INF, "acima do limite")],  # meq/kg
    },
}

# ───────────────────────── QUANTITATIVO com LMR (resíduos/metais): limite único ─────────────────
# valor <= LMR → conforme ; acima → "acima do LMR" (alerta). Unidade mg/kg (ilustrativo).
LMR = {
    "residuos_agrotoxicos": {
        "clorpirifos": 0.01, "imidacloprido": 0.5, "glifosato": 0.1, "carbendazim": 0.1,
    },
    "metais_pesados": {
        "chumbo": 0.10, "cadmio": 0.05, "arsenio": 0.10, "mercurio": 0.01,
    },
}

# ───────────────────────── IDENTIFICAÇÃO: níveis de infestação (contagem) ────────────────────────
# Ilustrativo. Ex.: MAD (moscas/armadilha/dia) — nível de ação do MIP.
NIVEIS_CONTAGEM = {
    "default": [(0, 1, "baixo"), (1, 5, "medio"), (5, INF, "alto")],
}

# ───────────────────────── RECOMENDAÇÕES ─────────────────────────
RECOMENDACOES_QUANT = {
    ("fertilidade_solo", "ph", "muito baixo (acido)"): "Calagem recomendada para corrigir a acidez.",
    ("fertilidade_solo", "ph", "baixo"): "Avaliar calagem conforme a cultura.",
    ("fertilidade_solo", "fosforo", "baixo"): "Adubação fosfatada recomendada.",
    ("fertilidade_solo", "potassio", "baixo"): "Adubação potássica recomendada.",
    ("fertilidade_solo", "materia_organica", "baixo"): "Adubação orgânica / cobertura vegetal.",
    ("analise_foliar", "nitrogenio", "baixo"): "Revisar adubação nitrogenada.",
}

# para qualquer analito com classe "acima do LMR"/"acima do limite"/"fora do padrao"
RECOMENDACAO_NAO_CONFORME = "Resultado fora do padrão — investigar fonte e reanalisar."

DIAGNOSTICO_RECOMENDACAO = {
    "hlb": "POSITIVO p/ HLB (Greening): notificar a ADAB, erradicar a planta e manejar o psilídeo vetor.",
    "cvc": "POSITIVO p/ CVC: poda/erradicação e controle da cigarrinha vetora.",
    "cabmv": "POSITIVO p/ CABMV: eliminar plantas-fonte e controlar afídeos vetores.",
    "_default": "Resultado POSITIVO: acionar protocolo fitossanitário e notificar a defesa agropecuária.",
}

RECOMENDACAO_INFESTACAO = {
    "alto": "Nível de ação atingido: acionar Manejo Integrado de Pragas (ex.: Técnica do Inseto Estéril).",
    "medio": "Intensificar monitoramento e medidas preventivas.",
}
