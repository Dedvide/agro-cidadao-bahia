"""
Enriquece a malha REAL dos municípios da Bahia (IBGE) com os dados do CETAB.
Gera painel/bahia-municipios.geojson (coroplético) + painel/bahia-uf.geojson (contorno).

Pré-requisito: baixar do IBGE para saida/ (já feito):
  saida/bahia-uf.geojson · saida/bahia-mun-raw.geojson · saida/ba-lista.json

Rode:  python gerar_mapa_bahia.py
"""
import json
import shutil
import unicodedata
from pathlib import Path

from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
SAIDA = AQUI / "saida"
PAINEL = AQUI.parent / "painel"
Q, D = TipoResultado.quantitativo, TipoResultado.diagnostico


def norm(s):
    nf = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in nf if not unicodedata.combining(c))


# ── 1) dados do CETAB por município (mesma base da demo) ──
DB = SAIDA / "mapa_bahia.sqlite"
if DB.exists():
    DB.unlink()
conn = conectar(DB)


def solo(mun, sol, ph, p, k, mo):
    salvar(conn, Laudo(laudo_id=mun, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
        municipio=mun, solicitante_tipo=sol, data_coleta="2026-04-10", laboratorio="CETAB",
        resultados=[Resultado(tipo=Q, analito="ph", valor=ph), Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="materia_organica", valor=mo, unidade="%")], confianca_geral=0.95))


solo("Barreiras", TipoSolicitante.produtor_rural, 4.8, 6, 28, 1.1)
solo("Barreiras", TipoSolicitante.produtor_rural, 5.0, 7, 30, 1.3)
solo("Luis Eduardo Magalhaes", TipoSolicitante.produtor_rural, 5.2, 9, 38, 1.5)
solo("Cruz das Almas", TipoSolicitante.agricultura_familiar, 5.2, 8, 35, 1.4)
solo("Juazeiro", TipoSolicitante.cooperativa, 6.8, 40, 120, 2.0)
solo("Muritiba", TipoSolicitante.agricultura_familiar, 4.9, 5, 22, 1.0)
solo("Santo Antonio de Jesus", TipoSolicitante.produtor_rural, 6.4, 35, 110, 3.2)
salvar(conn, Laudo(laudo_id="GM", categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
    municipio="Governador Mangabeira", solicitante_tipo=TipoSolicitante.produtor_rural, data_coleta="2026-04-12",
    resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")], confianca_geral=0.95))

dados = {}
for r in conn.execute(
    """SELECT l.municipio mun, COUNT(DISTINCT l.id) n,
              COUNT(DISTINCT CASE WHEN r.alerta=1 THEN l.id END) a
       FROM laudo l LEFT JOIN resultado r ON r.laudo_fk=l.id GROUP BY l.municipio""").fetchall():
    dados[norm(r["mun"])] = {"n": r["n"], "alertas": r["a"]}
conn.close()

# ── 2) mapa codarea(IBGE) -> nome ──
lista = json.loads((SAIDA / "ba-lista.json").read_text(encoding="utf-8"))
cod_nome = {str(m["id"]): m["nome"] for m in lista}

# ── 3) enriquece a malha ──
malha = json.loads((SAIDA / "bahia-mun-raw.geojson").read_text(encoding="utf-8"))
com_dados = 0
for f in malha["features"]:
    p = f.get("properties", {})
    cod = str(p.get("codarea") or p.get("id") or f.get("id") or "")
    nome = cod_nome.get(cod, p.get("nome") or cod)
    d = dados.get(norm(nome))
    f["properties"] = {
        "nome": nome,
        "tem_dados": bool(d),
        "n_laudos": d["n"] if d else 0,
        "alertas": d["alertas"] if d else 0,
        "taxa_alerta": round(d["alertas"] / d["n"], 2) if d and d["n"] else 0,
    }
    if d:
        com_dados += 1

(PAINEL / "bahia-municipios.geojson").write_text(json.dumps(malha, ensure_ascii=False), encoding="utf-8")
shutil.copy(SAIDA / "bahia-uf.geojson", PAINEL / "bahia-uf.geojson")

print(f"Mapa da Bahia gerado: {len(malha['features'])} municípios reais (IBGE)")
print(f"  {com_dados} municípios com dados do CETAB cruzados")
print("  -> painel/bahia-municipios.geojson + painel/bahia-uf.geojson")
