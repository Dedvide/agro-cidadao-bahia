"""
Gera os dados do PAINEL (sem API) cobrindo os 5 EIXOS do CETAB com dados genéricos,
em volume e datas variados para os gráficos fazerem sentido.
Exporta amostras.geojson + indicadores.json direto em ../painel/.

Rode:  python gerar_painel_demo.py
Depois:  cd ../painel ; python -m http.server 8000
"""
from pathlib import Path

import consultar
from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

RAIZ = Path(__file__).parent.parent
PAINEL = RAIZ / "painel"
PAINEL.mkdir(exist_ok=True)
DB = Path(__file__).parent / "saida" / "datalake_painel.sqlite"
DB.parent.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

Q = TipoResultado.quantitativo
D = TipoResultado.diagnostico
I = TipoResultado.identificacao
AF = TipoSolicitante.agricultura_familiar
PR = TipoSolicitante.produtor_rural
CO = TipoSolicitante.cooperativa
PF = TipoSolicitante.prefeitura


def base(lid, cat, amostra, mun, sol, data, resultados, conf=0.95):
    return Laudo(
        laudo_id=lid, categoria_analise=cat, tipo_amostra=amostra, municipio=mun,
        solicitante_tipo=sol, data_coleta=data, laboratorio="CETAB",
        resultados=resultados, confianca_geral=conf,
        campos_incertos=[] if conf >= 0.7 else ["unidade"],
    )


def solo(lid, mun, sol, data, ph, p, k, mo, conf=0.95):
    return base(lid, "fertilidade_solo", TipoAmostra.solo, mun, sol, data, [
        Resultado(tipo=Q, analito="ph", valor=ph, metodo="agua"),
        Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3", metodo="Mehlich-1"),
        Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
        Resultado(tipo=Q, analito="materia_organica", valor=mo, unidade="%"),
    ], conf)


def agua(lid, mun, sol, data, ph, turb, colif):
    return base(lid, "analise_agua", TipoAmostra.agua, mun, sol, data, [
        Resultado(tipo=Q, analito="ph", valor=ph),
        Resultado(tipo=Q, analito="turbidez", valor=turb, unidade="UNT"),
        Resultado(tipo=Q, analito="coliformes_termotolerantes", valor=colif, unidade="NMP/100mL"),
    ])


def residuo(lid, mun, sol, data, clorp, imid, carb):
    return base(lid, "residuos_agrotoxicos", TipoAmostra.fruto, mun, sol, data, [
        Resultado(tipo=Q, analito="clorpirifos", valor=clorp, unidade="mg/kg"),
        Resultado(tipo=Q, analito="imidacloprido", valor=imid, unidade="mg/kg"),
        Resultado(tipo=Q, analito="carbendazim", valor=carb, unidade="mg/kg"),
    ])


def mel(lid, mun, sol, data, umid, hmf, acidez):
    return base(lid, "qualidade_alimentos", TipoAmostra.mel, mun, sol, data, [
        Resultado(tipo=Q, analito="umidade", valor=umid, unidade="%"),
        Resultado(tipo=Q, analito="hmf", valor=hmf, unidade="mg/kg"),
        Resultado(tipo=Q, analito="acidez", valor=acidez, unidade="meq/kg"),
    ])


def molecular(lid, mun, sol, data, hlb, ct=None, cvc="negativo"):
    return base(lid, "diagnostico_molecular", TipoAmostra.foliar, mun, sol, data, [
        Resultado(tipo=D, alvo="hlb", resultado_diagnostico=hlb, ct=ct, metodo="qPCR"),
        Resultado(tipo=D, alvo="cvc", resultado_diagnostico=cvc, metodo="qPCR"),
    ])


def moscas(lid, mun, sol, data, ceratitis, anastrepha, conf=0.95):
    return base(lid, "monitoramento_pragas", TipoAmostra.inseto, mun, sol, data, [
        Resultado(tipo=I, taxon="Ceratitis capitata", contagem=ceratitis, estagio="adulto"),
        Resultado(tipo=I, taxon="Anastrepha fraterculus", contagem=anastrepha, estagio="adulto"),
    ], conf)


LAUDOS = [
    # ── Fertilidade de solo ──
    solo("2026/0457", "Cruz das Almas", AF, "2026-01-12", 5.2, 8, 35, 1.4),
    solo("2026/0461", "Muritiba", PR, "2026-01-20", 4.8, 5, 28, 1.1, conf=0.6),
    solo("2026/0470", "Santo Antonio de Jesus", CO, "2026-02-05", 6.4, 35, 110, 3.2),
    solo("2026/0480", "Governador Mangabeira", PR, "2026-02-18", 5.6, 18, 70, 2.5),
    solo("2026/0491", "Sao Felix", AF, "2026-03-03", 5.0, 6, 30, 1.2),
    solo("2026/0503", "Feira de Santana", PR, "2026-03-22", 6.0, 24, 85, 2.9),
    solo("2026/0512", "Cachoeira", AF, "2026-04-09", 4.9, 7, 26, 1.0),
    # ── Qualidade da água ──
    agua("2026/AG-204", "Cachoeira", PF, "2026-02-11", 7.2, 8.5, 3),
    agua("2026/AG-218", "Sao Felix", PF, "2026-04-15", 6.8, 3.0, 0),
    # ── Resíduos de agrotóxicos ──
    residuo("2026/RES-77", "Muritiba", CO, "2026-03-10", 0.03, 0.2, 0.05),   # clorpirifos > LMR
    residuo("2026/RES-90", "Santo Antonio de Jesus", CO, "2026-05-02", 0.005, 0.1, 0.04),
    # ── Qualidade de alimentos (mel de cacau) ──
    mel("2026/MEL-12", "Cruz das Almas", CO, "2026-04-22", 18.5, 25, 35),
    mel("2026/MEL-19", "Governador Mangabeira", AF, "2026-05-08", 21.0, 70, 55),  # fora do padrão
    # ── Diagnóstico molecular (HLB/CVC) ──
    molecular("2026/MOL-58", "Governador Mangabeira", PR, "2026-03-28", "positivo", ct=27.4),  # alerta
    molecular("2026/MOL-61", "Santo Antonio de Jesus", PR, "2026-04-30", "negativo"),
    molecular("2026/MOL-66", "Cruz das Almas", AF, "2026-05-12", "positivo", ct=31.0),         # alerta
    # ── Monitoramento de moscas-das-frutas ──
    moscas("2026/ENT-33", "Sao Felix", PR, "2026-03-15", 14, 3),       # alto → alerta
    moscas("2026/ENT-40", "Feira de Santana", PR, "2026-04-18", 1, 0, conf=0.65),
    moscas("2026/ENT-47", "Muritiba", AF, "2026-05-20", 8, 2),         # alto → alerta
]


def main() -> int:
    conn = conectar(DB)
    for lau in LAUDOS:
        salvar(conn, lau)

    n = consultar.exportar_geojson(conn, PAINEL / "amostras.geojson")
    ind = consultar.exportar_indicadores(conn, PAINEL / "indicadores.json")

    # Núcleo Científico (Módulo 11): dataset de pesquisa FAIR-ready
    ds_base = Path(__file__).parent / "saida" / "dataset_pesquisa"
    n_linhas = consultar.exportar_dataset_pesquisa(conn, ds_base, gerado_em="2026-06-03T00:00:00")
    conn.close()

    e = ind["indicadores_enap"]
    print(f"Gerados em {PAINEL.name}/:  amostras.geojson ({n} pontos)")
    print(f"  {ind['total_laudos']} laudos · {ind['municipios_cobertos']} municípios · "
          f"{len(ind['por_categoria'])} eixos · {ind['laudos_com_alerta']} com alerta")
    print(f"  KPIs ENAP: {e['alertas_emitidos']} alertas · "
          f"{e['pct_agricultura_familiar']}% agric. familiar · "
          f"~{e['tempo_estimado_economizado_h']}h economizadas (estimativa)")
    print(f"  Recomendações automáticas: {len(ind['recomendacoes'])}")
    print(f"  Dataset de pesquisa (Módulo 11): {n_linhas} linhas -> saida/dataset_pesquisa.csv")
    print("    + dicionario.json + proveniencia.json (FAIR-ready)")
    print("\nVisualizar:  cd ../painel ; python -m http.server 8000 ; abra http://localhost:8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
