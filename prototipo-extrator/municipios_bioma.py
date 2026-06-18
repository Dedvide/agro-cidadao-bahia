"""
SSOT (fonte única) dos municípios do projeto ABC+ / PRODEAGRO — Ofício SEAGRI 464/2026.

3 biomas × 10 municípios reais, com as culturas/tecnologias do projeto.
Usado pelo gerador de dados, pelo CRM e pelo Painel de Metas ABC+.
"""
import unicodedata

# 10 municípios reais do projeto, por bioma (Ofício, territorialização)
ABC = {
    "Caatinga": ["Juazeiro", "Casa Nova", "Irecê"],
    "Cerrado (Chapada Diamantina)": ["Palmeiras", "Mucugê", "Ibicoara", "Andaraí"],
    "Mata Atlântica": ["Tancredo Neves", "Itabuna", "Teixeira de Freitas"],
}

# culturas/tecnologias ABC+ típicas por bioma
CULTURAS = {
    "Caatinga": ["feijão", "milho", "sorgo", "fruticultura irrigada", "palma forrageira"],
    "Cerrado (Chapada Diamantina)": ["café", "horticultura", "grãos", "fruticultura"],
    "Mata Atlântica": ["cacau cabruca", "mandioca", "café", "SAF"],
}
TECNOLOGIAS_ABC = ["recuperação de áreas degradadas", "ILPF", "SAFs", "plantio direto",
                   "bioinsumos", "rotação de culturas"]


def _norm(s):
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


_REV = {}
for _bioma, _muns in ABC.items():
    for _m in _muns:
        _REV[_norm(_m)] = _bioma


def bioma_de(municipio: str) -> str | None:
    return _REV.get(_norm(municipio))


def todos() -> list[tuple[str, str]]:
    """Lista [(municipio, bioma)] dos 10 municípios."""
    return [(m, b) for b, ms in ABC.items() for m in ms]
