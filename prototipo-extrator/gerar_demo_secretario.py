"""
Gera a DEMO DO SECRETÁRIO (modo offline, sem API):
  - demo-institucional.json : números-manchete do CETAB (a confirmar)
  - demo-laudos.json        : laudos de exemplo JÁ interpretados pelo motor real
  - demo-chat.json          : perguntas + respostas calculadas sobre o Data Lake

Tudo é pré-computado para a reunião não depender de internet/IA ao vivo.
A interpretação usa o MESMO motor (interpretar.py) — só está pré-renderizada.

Rode:  python gerar_demo_secretario.py
"""
import json
from pathlib import Path

import consultar
from interpretar import interpretar_laudo
from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
PAINEL = AQUI.parent / "painel"
DB = AQUI / "saida" / "demo_secretario.sqlite"
DB.parent.mkdir(exist_ok=True)
PAINEL.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

Q, D = TipoResultado.quantitativo, TipoResultado.diagnostico

# ───────── números-manchete (CONFIRMAR com o CETAB) ─────────
INSTITUCIONAL = {
    "ano": 2024, "analises": 107000, "laudos": 9566, "municipios": "estadual",
    "laboratorios": 8, "nota": "Números a CONFIRMAR nos registros oficiais do CETAB.",
}

conn = conectar(DB)


def solo(lid, mun, sol, ph, p, k, mo):
    salvar(conn, Laudo(laudo_id=lid, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
        municipio=mun, solicitante_tipo=sol, data_coleta="2026-04-10", laboratorio="CETAB",
        resultados=[Resultado(tipo=Q, analito="ph", valor=ph),
                    Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="materia_organica", valor=mo, unidade="%")],
        confianca_geral=0.95))


# Data Lake da demo (variado, com casos de alerta)
solo("S1", "Barreiras", TipoSolicitante.produtor_rural, 4.8, 6, 28, 1.1)
solo("S2", "Barreiras", TipoSolicitante.produtor_rural, 5.0, 7, 30, 1.3)
solo("S3", "Luis Eduardo Magalhaes", TipoSolicitante.produtor_rural, 5.2, 9, 38, 1.5)
solo("S4", "Cruz das Almas", TipoSolicitante.agricultura_familiar, 5.2, 8, 35, 1.4)
solo("S5", "Juazeiro", TipoSolicitante.cooperativa, 6.8, 40, 120, 2.0)
solo("S6", "Muritiba", TipoSolicitante.agricultura_familiar, 4.9, 5, 22, 1.0)
solo("S7", "Santo Antonio de Jesus", TipoSolicitante.produtor_rural, 6.4, 35, 110, 3.2)
salvar(conn, Laudo(laudo_id="M1", categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
    municipio="Governador Mangabeira", solicitante_tipo=TipoSolicitante.produtor_rural, data_coleta="2026-04-12",
    resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")],
    confianca_geral=0.95))

# ───────── 1) demo-laudos.json (documento bruto + interpretação real) ─────────
def laudo_obj(titulo, tipo_txt, bruto, laudo):
    its = interpretar_laudo(laudo)
    alertas = [it for it in its if it.alerta]
    resumo = ("Sem pontos críticos." if not alertas else
              "Requer atenção: " + "; ".join(f"{it.rotulo} ({it.classe})" for it in alertas) + ".")
    return {
        "titulo": titulo, "tipo": tipo_txt, "documento_bruto": bruto,
        "resumo": resumo,
        "resultados": [{"rotulo": it.rotulo, "valor": it.valor_exibicao, "classe": it.classe,
                        "alerta": it.alerta, "recomendacao": it.recomendacao} for it in its],
    }


laudo_solo = Laudo(laudo_id="2026/0457", categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
    municipio="Cruz das Almas", solicitante_tipo=TipoSolicitante.agricultura_familiar,
    resultados=[Resultado(tipo=Q, analito="ph", valor=4.8), Resultado(tipo=Q, analito="fosforo", valor=8, unidade="mg/dm3"),
                Resultado(tipo=Q, analito="potassio", valor=35, unidade="mg/dm3"),
                Resultado(tipo=Q, analito="materia_organica", valor=1.4, unidade="%")], confianca_geral=0.95)
laudo_hlb = Laudo(laudo_id="2026/MOL-58", categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
    municipio="Governador Mangabeira", solicitante_tipo=TipoSolicitante.produtor_rural,
    resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")], confianca_geral=0.95)

demo_laudos = [
    laudo_obj("Análise de solo — Sítio Boa Esperança (Cruz das Almas)", "Fertilidade de solo",
        "CETAB - Lab. de Solos\nLaudo 2026/0457\npH (água): 4,8\nFósforo (P): 8 mg/dm3\n"
        "Potássio (K): 35 mg/dm3\nMatéria orgânica: 1,4 %", laudo_solo),
    laudo_obj("Diagnóstico molecular — folha de citros (Gov. Mangabeira)", "Biologia molecular (qPCR)",
        "CETAB - Biologia Molecular\nLaudo 2026/MOL-58\nMétodo: qPCR\n"
        "Pesquisa de HLB (Candidatus Liberibacter): POSITIVO (Ct 27,4)", laudo_hlb),
]
(PAINEL / "demo-laudos.json").write_text(json.dumps(demo_laudos, ensure_ascii=False, indent=2), encoding="utf-8")

# ───────── 2) demo-chat.json (respostas reais sobre o Data Lake) ─────────
def municipios_classe(analito, classe):
    linhas = conn.execute(
        """SELECT DISTINCT l.municipio FROM resultado r JOIN laudo l ON l.id=r.laudo_fk
           WHERE LOWER(r.rotulo)=? AND r.classe=?""", (analito, classe)).fetchall()
    return [x[0] for x in linhas]

total = conn.execute("SELECT COUNT(*) FROM laudo").fetchone()[0]
fosf_baixo = municipios_classe("fosforo", "baixo")
pot_baixo = municipios_classe("potassio", "baixo")
hlb_pos = [x[0] for x in conn.execute(
    "SELECT DISTINCT l.municipio FROM resultado r JOIN laudo l ON l.id=r.laudo_fk WHERE r.alvo='hlb' AND r.resultado_diagnostico='positivo'").fetchall()]
por_cat = conn.execute(
    """SELECT l.categoria_analise, COUNT(DISTINCT CASE WHEN r.alerta=1 THEN l.id END) a
       FROM laudo l LEFT JOIN resultado r ON r.laudo_fk=l.id GROUP BY l.categoria_analise ORDER BY a DESC""").fetchall()

demo_chat = [
    {"pergunta": "Quantas análises o CETAB realizou?", "tags": ["quantas", "analises", "total", "realizou"],
     "resposta": f"Em {INSTITUCIONAL['ano']}, o CETAB realizou aproximadamente {INSTITUCIONAL['analises']:,} análises "
                 f"e emitiu {INSTITUCIONAL['laudos']:,} laudos, em {INSTITUCIONAL['laboratorios']} laboratórios "
                 f"com cobertura estadual.".replace(",", ".")},
    {"pergunta": "Quais municípios têm deficiência de fósforo no solo?", "tags": ["municipios", "fosforo", "deficiencia", "baixo"],
     "resposta": ("Municípios com fósforo baixo nas amostras: " + ", ".join(fosf_baixo) + "."
                  if fosf_baixo else "Nenhum município com fósforo baixo nas amostras atuais.")},
    {"pergunta": "Quais municípios têm deficiência de potássio?", "tags": ["municipios", "potassio", "deficiencia"],
     "resposta": ("Municípios com potássio baixo: " + ", ".join(pot_baixo) + "."
                  if pot_baixo else "Nenhum município com potássio baixo nas amostras atuais.")},
    {"pergunta": "Onde há diagnóstico positivo de HLB (greening)?", "tags": ["hlb", "greening", "positivo", "citros", "doenca"],
     "resposta": ("Diagnóstico POSITIVO para HLB em: " + ", ".join(hlb_pos) +
                  ". Recomenda-se notificar a ADAB e manejar o vetor." if hlb_pos else "Sem HLB positivo nas amostras.")},
    {"pergunta": "Quais áreas apresentam maior risco fitossanitário?", "tags": ["risco", "fitossanitario", "culturas", "eixo", "maior"],
     "resposta": "Eixos com mais amostras em alerta: " +
                 ", ".join(f"{c[0]} ({c[1]})" for c in por_cat if c[1]) + "."},
    {"pergunta": "Qual o panorama geral?", "tags": ["panorama", "geral", "resumo", "estado"],
     "resposta": f"Base atual: {total} laudos analisados. Fósforo baixo em {len(fosf_baixo)} município(s); "
                 f"HLB positivo em {len(hlb_pos)}. O sistema transforma os laudos em mapa de risco e recomendações."},
]
(PAINEL / "demo-chat.json").write_text(json.dumps(demo_chat, ensure_ascii=False, indent=2), encoding="utf-8")
(PAINEL / "demo-institucional.json").write_text(json.dumps(INSTITUCIONAL, ensure_ascii=False, indent=2), encoding="utf-8")

# também atualiza o mapa/dashboard com este Data Lake (para coerência da demo)
consultar.exportar_geojson(conn, PAINEL / "amostras.geojson")
consultar.exportar_indicadores(conn, PAINEL / "indicadores.json")
conn.close()

print("Demo do secretário gerada em painel/:")
print(f"  demo-laudos.json ({len(demo_laudos)} laudos interpretados)")
print(f"  demo-chat.json ({len(demo_chat)} perguntas) · demo-institucional.json")
print(f"  + amostras.geojson / indicadores.json atualizados")
print("\nVisualizar:  cd ../painel ; python -m http.server 8000")
print("  Telas: /  (dashboard+mapa) · /laudo.html · /assistente.html")
