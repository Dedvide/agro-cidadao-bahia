"""
Monitoramento Ambiental — clima/satélite/sensores para risco fitossanitário.

Núcleo FUNCIONAL: base climática (seed) por município + heurística de risco
(ex.: umidade alta + temperatura amena → risco de doença fúngica/HLB).
STUBS documentados para as fontes vivas (já desenhadas na Camada de Integração do plano).

Roda OFFLINE.
"""
from __future__ import annotations

import unicodedata

# Seed climático (médias ilustrativas). Em produção: INMET/Agritempo (séries reais).
CLIMA_SEED = {
    "cruz das almas": {"temp": 24.5, "umidade": 82, "precip_mm": 110},
    "juazeiro": {"temp": 27.8, "umidade": 55, "precip_mm": 20},
    "cachoeira": {"temp": 25.1, "umidade": 80, "precip_mm": 95},
    "governador mangabeira": {"temp": 24.8, "umidade": 84, "precip_mm": 120},
    "sao felix": {"temp": 25.0, "umidade": 81, "precip_mm": 100},
    # municípios do projeto ABC+ (por bioma)
    "casa nova": {"temp": 28.2, "umidade": 52, "precip_mm": 18},
    "irece": {"temp": 24.5, "umidade": 58, "precip_mm": 35},
    "palmeiras": {"temp": 22.0, "umidade": 76, "precip_mm": 90},
    "mucuge": {"temp": 21.5, "umidade": 75, "precip_mm": 85},
    "ibicoara": {"temp": 21.0, "umidade": 78, "precip_mm": 95},
    "andarai": {"temp": 23.0, "umidade": 74, "precip_mm": 80},
    "tancredo neves": {"temp": 24.8, "umidade": 83, "precip_mm": 130},
    "itabuna": {"temp": 24.9, "umidade": 84, "precip_mm": 140},
    "teixeira de freitas": {"temp": 24.2, "umidade": 80, "precip_mm": 120},
}


def _na(s: str) -> str:
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


def clima_municipio(municipio: str) -> dict | None:
    return CLIMA_SEED.get(_na(municipio))


def risco_fitossanitario(clima: dict) -> dict:
    """Heurística simples de risco a partir do clima (ilustrativa)."""
    if not clima:
        return {"nivel": "desconhecido", "motivo": "sem dado climático"}
    u, t = clima["umidade"], clima["temp"]
    if u >= 80 and 20 <= t <= 28:
        return {"nivel": "alto", "motivo": "umidade alta + temperatura amena (favorável a fungos/vetores)"}
    if u >= 70:
        return {"nivel": "medio", "motivo": "umidade moderada-alta"}
    return {"nivel": "baixo", "motivo": "condições menos favoráveis a patógenos"}


def avaliar_municipio(municipio: str) -> dict:
    clima = clima_municipio(municipio)
    return {"municipio": municipio, "clima": clima, "risco": risco_fitossanitario(clima)}


# ───────── STUBS: fontes vivas (ver Camada de Integração no PLANO-MESTRE) ─────────

def inmet_estacao(codigo: str):
    """STUB. INMET — API pública de estações automáticas (dados horários)."""
    raise NotImplementedError("Integração INMET — Fase 3.")


def satveg_ndvi(lat: float, lon: float):
    """STUB. Embrapa SATVeg (AgroAPI) — série NDVI/EVI por ponto."""
    raise NotImplementedError("Integração SATVeg/AgroAPI — Fase 3.")


def inpe_queimadas(municipio: str):
    """STUB. INPE — focos de calor (BDQueimadas)."""
    raise NotImplementedError("Integração INPE — Fase 3.")


def _demo():
    print("=== MONITORAMENTO AMBIENTAL ===")
    for mun in ["Cruz das Almas", "Juazeiro", "Governador Mangabeira"]:
        a = avaliar_municipio(mun)
        c = a["clima"]
        clima_txt = f"{c['temp']}°C, {c['umidade']}% UR" if c else "sem dado"
        print(f"  {mun}: {clima_txt} -> risco {a['risco']['nivel'].upper()} ({a['risco']['motivo']})")
    print("Monitoramento ambiental: OK")


if __name__ == "__main__":
    _demo()
