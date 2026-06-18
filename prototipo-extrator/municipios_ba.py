"""
Centroides (lat, long) de municípios da Bahia — para georreferenciar amostras
sem coordenada explícita no laudo.

Protótipo: tabela estática com alguns municípios. Em produção, usar a malha
oficial do IBGE (todos os 417 municípios baianos) carregada no PostGIS.
"""
import unicodedata

# (latitude, longitude) aproximados do centro do município
CENTROIDES = {
    "cruz das almas": (-12.6706, -39.1018),
    "cachoeira": (-12.6028, -38.9664),
    "santo antonio de jesus": (-12.9690, -39.2618),
    "sao felix": (-12.6086, -38.9722),
    "muritiba": (-12.6261, -39.0292),
    "governador mangabeira": (-12.6000, -39.0419),
    "feira de santana": (-12.2664, -38.9663),
    "salvador": (-12.9714, -38.5014),
    # municípios do projeto ABC+ / PRODEAGRO (3 biomas)
    "juazeiro": (-9.4111, -40.4986),
    "casa nova": (-9.1631, -40.9706),
    "irece": (-11.3044, -41.8558),
    "palmeiras": (-12.5089, -41.5775),
    "mucuge": (-13.0050, -41.3711),
    "ibicoara": (-13.4100, -41.2850),
    "andarai": (-12.8067, -41.3300),
    "tancredo neves": (-13.4500, -39.4231),
    "itabuna": (-14.7856, -39.2803),
    "teixeira de freitas": (-17.5394, -39.7425),
}


def _normalizar(nome: str) -> str:
    nfkd = unicodedata.normalize("NFKD", nome.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def centroide(municipio: str | None) -> tuple[float, float] | tuple[None, None]:
    if not municipio:
        return (None, None)
    chave = _normalizar(municipio).replace(" - ba", "").replace("/ba", "").strip()
    return CENTROIDES.get(chave, (None, None))
