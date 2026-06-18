"""Teste offline (sem API) do Data Lake: salvar -> consolidar -> exportar GeoJSON."""
from pathlib import Path

import consultar
from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoSolicitante

PASTA = Path(__file__).parent
DB = PASTA / "saida" / "datalake_teste.sqlite"
GEOJSON = PASTA / "saida" / "amostras.geojson"
DB.parent.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()


def laudo(lid, mun, tipo, fosforo, ph, conf=0.95):
    return Laudo(
        laudo_id=lid,
        categoria_analise="fertilidade_solo",
        tipo_amostra=TipoAmostra.solo,
        municipio=mun,
        solicitante_tipo=tipo,
        data_coleta="2026-03-12",
        resultados=[
            Resultado(analito="ph", valor=ph),
            Resultado(analito="fosforo", valor=fosforo, unidade="mg/dm3"),
        ],
        confianca_geral=conf,
        campos_incertos=[] if conf >= 0.7 else ["unidade"],
    )


conn = conectar(DB)
# Simula 4 laudos de municípios diferentes (o que o extrator IA produziria)
salvar(conn, laudo("2026/0457", "Cruz das Almas", TipoSolicitante.agricultura_familiar, 8, 5.2))
salvar(conn, laudo("A-1187", "Cachoeira", TipoSolicitante.produtor_rural, 22, 6.1))
salvar(conn, laudo("2026/0461", "Muritiba", TipoSolicitante.produtor_rural, 5, 4.8, conf=0.6))
salvar(conn, laudo("2026/0470", "Santo Antonio de Jesus", TipoSolicitante.cooperativa, 35, 6.4))

r = consultar.resumo(conn)
print("=== RESUMO DO DATA LAKE ===")
print(f"  Total de laudos:        {r['total_laudos']}")
print(f"  Municípios cobertos:    {r['municipios_cobertos']}")
print(f"  Aguardando revisão:     {r['aguardando_revisao_humana']}")
print("  Por município:")
for mun, n in r["por_municipio"]:
    print(f"    - {mun}: {n}")

print("\n=== DISTRIBUIÇÃO: fósforo no solo ===")
for classe, n in consultar.distribuicao_classe(conn, "fosforo"):
    print(f"  {classe:14} {n}")

n_pontos = consultar.exportar_geojson(conn, GEOJSON)
print(f"\n=== MAPA ===")
print(f"  GeoJSON exportado: {n_pontos} pontos georreferenciados -> {GEOJSON.name}")
print("  (abre direto em QGIS / Leaflet / Mapbox)")
conn.close()
print("\nData Lake + consolidação + geo: OK")
