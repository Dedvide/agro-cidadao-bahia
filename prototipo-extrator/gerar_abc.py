"""
Gerador da demo ABC+ / PRODEAGRO — re-semeia o Data Lake nos 10 municípios reais
(3 biomas) do Ofício SEAGRI 464/2026 e re-exporta tudo que o painel consome.

Rode:  python gerar_abc.py
"""
from pathlib import Path

import consultar
import mapa_bahia
from municipios_bioma import bioma_de, todos
from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
PAINEL = AQUI.parent / "painel"
DB = AQUI / "saida" / "datalake_painel.sqlite"  # banco padrão lido pela API/painel
DB.parent.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

Q, D = TipoResultado.quantitativo, TipoResultado.diagnostico
conn = conectar(DB)


def solo(lid, mun, sol, ph, p, k, mo):
    salvar(conn, Laudo(laudo_id=lid, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
        municipio=mun, solicitante_tipo=sol, data_coleta="2026-04-10", laboratorio="CETAB - Lab. de Solos",
        resultados=[Resultado(tipo=Q, analito="ph", valor=ph),
                    Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="materia_organica", valor=mo, unidade="%")],
        confianca_geral=0.95))


def agua(lid, mun, ph, turb):
    salvar(conn, Laudo(laudo_id=lid, categoria_analise="analise_agua", tipo_amostra=TipoAmostra.agua,
        municipio=mun, solicitante_tipo=TipoSolicitante.prefeitura, data_coleta="2026-04-12", laboratorio="CETAB",
        resultados=[Resultado(tipo=Q, analito="ph", valor=ph),
                    Resultado(tipo=Q, analito="turbidez", valor=turb, unidade="UNT")], confianca_geral=0.9))


# valores variados por bioma (alguns disparam alerta: solo ácido / P baixo)
PERFIL = {
    "Caatinga": (6.2, 18, 90, 1.6, 7.1, 4.0),
    "Cerrado (Chapada Diamantina)": (5.0, 8, 40, 1.3, 6.8, 6.0),  # solo ácido + P baixo -> alerta
    "Mata Atlântica": (4.8, 6, 35, 2.4, 6.5, 9.0),                # solo ácido + P baixo -> alerta
}

for i, (mun, bioma) in enumerate(todos(), start=1):
    ph, p, k, mo, agph, agt = PERFIL[bioma]
    solo(f"ABC-S{i:02d}", mun, TipoSolicitante.agricultura_familiar, ph, p, k, mo)
    solo(f"ABC-S{i:02d}b", mun, TipoSolicitante.produtor_rural, ph + 0.4, p + 6, k + 20, mo + 0.3)
    agua(f"ABC-A{i:02d}", mun, agph, agt)

# diagnóstico molecular (Mata Atlântica — citros/cacau): HLB positivo em Itabuna
salvar(conn, Laudo(laudo_id="ABC-MOL-01", categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
    municipio="Itabuna", solicitante_tipo=TipoSolicitante.produtor_rural, data_coleta="2026-04-15",
    resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")],
    confianca_geral=0.95))

# dados por município (para o coroplético)
dados = {}
for r in conn.execute(
    """SELECT l.municipio mun, COUNT(DISTINCT l.id) n,
              COUNT(DISTINCT CASE WHEN r.alerta=1 THEN l.id END) a
       FROM laudo l LEFT JOIN resultado r ON r.laudo_fk=l.id GROUP BY l.municipio""").fetchall():
    import unicodedata
    nf = unicodedata.normalize("NFKD", r["mun"].lower())
    chave = "".join(c for c in nf if not unicodedata.combining(c))
    dados[chave] = {"n": r["n"], "alertas": r["a"]}

n_geo = consultar.exportar_geojson(conn, PAINEL / "amostras.geojson")
ind = consultar.exportar_indicadores(conn, PAINEL / "indicadores.json")
conn.close()

com = mapa_bahia.enriquecer_e_exportar(dados)

print("Demo ABC+ gerada (10 municípios, 3 biomas):")
print(f"  {ind['total_laudos']} laudos · {ind['municipios_cobertos']} municípios · {n_geo} pontos no mapa")
print(f"  coroplético: {com} municípios com dados")
print(f"  biomas: {list({bioma_de(m) for m, _ in todos()})}")
print("  -> painel/amostras.geojson, indicadores.json, bahia-municipios.geojson")
