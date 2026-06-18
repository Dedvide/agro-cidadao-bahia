"""
Helper reutilizável: enriquece a malha real dos municípios da Bahia (IBGE) com
dados do CETAB e exporta o coroplético para o painel. Usado por gerar_mapa_bahia
e gerar_abc (sem duplicar a lógica).

Requer em saida/: bahia-mun-raw.geojson, bahia-uf.geojson, ba-lista.json (download IBGE).
"""
import json
import shutil
import unicodedata
from pathlib import Path

AQUI = Path(__file__).parent
SAIDA = AQUI / "saida"
PAINEL = AQUI.parent / "painel"


def _norm(s):
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


def enriquecer_e_exportar(dados_por_municipio: dict) -> int:
    """
    dados_por_municipio: {norm(nome): {"n": int, "alertas": int}}.
    Escreve painel/bahia-municipios.geojson + bahia-uf.geojson. Retorna nº com dados.
    """
    lista = json.loads((SAIDA / "ba-lista.json").read_text(encoding="utf-8"))
    cod_nome = {str(m["id"]): m["nome"] for m in lista}
    malha = json.loads((SAIDA / "bahia-mun-raw.geojson").read_text(encoding="utf-8"))
    com = 0
    for f in malha["features"]:
        p = f.get("properties", {})
        cod = str(p.get("codarea") or p.get("id") or f.get("id") or "")
        nome = cod_nome.get(cod, p.get("nome") or cod)
        d = dados_por_municipio.get(_norm(nome))
        f["properties"] = {
            "nome": nome, "tem_dados": bool(d),
            "n_laudos": d["n"] if d else 0, "alertas": d["alertas"] if d else 0,
            "taxa_alerta": round(d["alertas"] / d["n"], 2) if d and d["n"] else 0,
        }
        if d:
            com += 1
    PAINEL.mkdir(exist_ok=True)
    (PAINEL / "bahia-municipios.geojson").write_text(json.dumps(malha, ensure_ascii=False), encoding="utf-8")
    shutil.copy(SAIDA / "bahia-uf.geojson", PAINEL / "bahia-uf.geojson")
    return com
