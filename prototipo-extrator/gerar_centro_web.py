"""
Gera os dados da página web "Centro de Pesquisa" (sem API): roda todos os módulos
novos e exporta painel/centro.json + painel/img/carta_controle.png.

Rode:  python gerar_centro_web.py
Depois:  cd ../painel ; python -m http.server 8000 ; abra http://localhost:8000/centro.html
"""
import json
from pathlib import Path

import bioinformatica
import biotecnologia
import descoberta
import equipamentos
import gestao_pesquisa
import monitoramento_ambiental
import qaqc
import repositorio
import visao_computacional
from persistencia import conectar, salvar
from schema import Laudo, Resultado, TipoAmostra, TipoResultado, TipoSolicitante

AQUI = Path(__file__).parent
PAINEL = AQUI.parent / "painel"
IMG = PAINEL / "img"
IMG.mkdir(parents=True, exist_ok=True)
DB = AQUI / "saida" / "centro.sqlite"
DB.parent.mkdir(exist_ok=True)
if DB.exists():
    DB.unlink()

Q, D, I = TipoResultado.quantitativo, TipoResultado.diagnostico, TipoResultado.identificacao
conn = conectar(DB)
for mod in (gestao_pesquisa, equipamentos, repositorio, biotecnologia):
    mod.garantir_tabelas(conn)


def solo(lid, mun, sol, ph, p, k, mo):
    salvar(conn, Laudo(laudo_id=lid, categoria_analise="fertilidade_solo", tipo_amostra=TipoAmostra.solo,
        municipio=mun, solicitante_tipo=sol, data_coleta="2026-04-10", laboratorio="CETAB",
        resultados=[Resultado(tipo=Q, analito="ph", valor=ph),
                    Resultado(tipo=Q, analito="fosforo", valor=p, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="potassio", valor=k, unidade="mg/dm3"),
                    Resultado(tipo=Q, analito="materia_organica", valor=mo, unidade="%")],
        confianca_geral=0.95))


# Data Lake (para descoberta/monitoramento) — solos variados + casos de alerta
solo("S1", "Cruz das Almas", TipoSolicitante.agricultura_familiar, 5.2, 8, 35, 1.4)
solo("S2", "Muritiba", TipoSolicitante.produtor_rural, 6.4, 35, 110, 3.2)
solo("S3", "Cachoeira", TipoSolicitante.agricultura_familiar, 4.9, 6, 26, 1.0)
solo("S4", "Sao Felix", TipoSolicitante.produtor_rural, 5.8, 18, 70, 2.5)
solo("S5", "Governador Mangabeira", TipoSolicitante.cooperativa, 6.0, 24, 85, 2.9)
salvar(conn, Laudo(laudo_id="M1", categoria_analise="diagnostico_molecular", tipo_amostra=TipoAmostra.foliar,
    municipio="Governador Mangabeira", solicitante_tipo=TipoSolicitante.produtor_rural, data_coleta="2026-04-12",
    resultados=[Resultado(tipo=D, alvo="hlb", resultado_diagnostico="positivo", ct=27.4, metodo="qPCR")],
    confianca_geral=0.95))

# Gestão de pesquisa
p1 = gestao_pesquisa.cadastrar_pesquisador(conn, "Dra. Marta Souza", orcid="0000-0002-1234-5678", area="Biologia Molecular")
p2 = gestao_pesquisa.cadastrar_pesquisador(conn, "Dr. Pedro Anjos", area="Entomologia")
ed = gestao_pesquisa.cadastrar_edital(conn, "Universal CNPq 2026", "CNPq", 2026, 150000)
pr = gestao_pesquisa.cadastrar_projeto(conn, "Epidemiologia do HLB no Recôncavo", "ativo", "CNPq", ed, "2026-01-01", "2027-12-31")
gestao_pesquisa.vincular_pesquisador(conn, pr, p1, "coordenador")
gestao_pesquisa.conceder_bolsa(conn, p2, pr, "Mestrado", 2100, "2026-2028")
gestao_pesquisa.vincular_publicacao(conn, pr, "10.1590/exemplo", "Dispersão do HLB em citros", 2026)
gestao_pesquisa.cadastrar_projeto(conn, "Mel de cacau: caracterização", "concluido", "FAPESB")

# Equipamentos & reagentes
equipamentos.cadastrar_equipamento(conn, "Termociclador qPCR", "CFX96", "Bio-Rad", "2025-06-01", "2026-06-01")
equipamentos.cadastrar_equipamento(conn, "Espectrômetro AA", "AA-7000", "Shimadzu", "2025-01-10", "2025-12-10")
equipamentos.cadastrar_reagente(conn, "Taq DNA Polimerase", "L2024A", "2026-12-31", 40, "U", 10)
equipamentos.cadastrar_reagente(conn, "Master Mix qPCR", "L2023X", "2026-01-15", 5, "mL", 10)

# Repositório
repositorio.registrar_documento(conn, "artigo", "Resistência da mangueira à antracnose (Colletotrichum)",
    "Genótipos de manga avaliados quanto à resistência à antracnose em alta umidade no semiárido.", doi="10.x/manga", ano=2024)
repositorio.registrar_documento(conn, "tese", "Epidemiologia do HLB em citros no Recôncavo Baiano",
    "Dispersão espacial do greening e do psilídeo vetor em pomares da Bahia.", ano=2025)
repositorio.registrar_documento(conn, "protocolo", "Detecção molecular de Xylella fastidiosa por qPCR",
    "Protocolo de extração e qPCR para diagnóstico de CVC em citros.", ano=2023)

# Biotecnologia
biotecnologia.registrar_cultura(conn, "CT-2026-01", "Citrus sinensis", "Pera", "segmento nodal", "MS", "multiplicacao", 480, 3.0, "2026-05-01")
biotecnologia.registrar_cultura(conn, "CT-2026-02", "Musa spp.", "Prata-Anã", "ápice caulinar", "MS", "enraizamento", 320, 15.0, "2026-05-08")
biotecnologia.registrar_bioproduto(conn, "BIO-01", "Trichoderma harzianum", "biocontrole", "1e9 UFC/g", 92, "2026-12-01")
biotecnologia.registrar_bioproduto(conn, "BIO-02", "Bacillus subtilis", "biocontrole", "1e8 UFC/mL", 70, "2026-02-01")
biotecnologia.registrar_germoplasma(conn, "GERM-114", "Manihot esculenta", "Recôncavo", "in vitro", 88)
biotecnologia.registrar_matriz(conn, "MZ-CT-07", "Citrus sinensis", "sadia", "HLB,CVC")
biotecnologia.registrar_matriz(conn, "MZ-CT-09", "Citrus sinensis", "infectada", "HLB")

# ── Monta centro.json ──
def doc_list():
    return [dict(d) for d in conn.execute("SELECT tipo,titulo,autores,doi,ano,texto FROM documento").fetchall()]

def proj_list():
    return [dict(p) for p in conn.execute("SELECT titulo,status,financiador FROM projeto").fetchall()]

def pesq_list():
    return [dict(p) for p in conn.execute("SELECT nome,area,orcid FROM pesquisador").fetchall()]

# bibliometria (lê seed do núcleo científico, se houver)
bib = {}
seed = AQUI.parent / "nucleo-cientifico" / "publicacoes_seed.json"
if seed.exists():
    pubs = json.loads(seed.read_text(encoding="utf-8"))["publicacoes"]
    anos = {}
    for p in pubs:
        anos[p["ano"]] = anos.get(p["ano"], 0) + 1
    bib = {"total": len(pubs), "por_ano": anos, "periodicos": len({p["periodico"] for p in pubs})}

# QA/QC
serie = [101, 99, 103, 98, 102, 100, 97, 118, 101, 99]
av = qaqc.avaliar_controle(serie, alvo=100, desvio=5)
qaqc.gerar_carta_lj(serie, 100, 5, IMG / "carta_controle.png")

centro = {
    "instituto": {**gestao_pesquisa.indicadores_institucionais(conn), "bibliometria": bib},
    "pesquisa": {"projetos": proj_list(), "pesquisadores": pesq_list()},
    "laboratorio": {
        "equipamentos_alertas": equipamentos.alertas(conn, hoje="2026-06-04"),
        "qaqc": {"status": av["status"], "violacoes": [list(v[:1]) + [v[2]] for v in av["violacoes"]],
                 "grafico": "img/carta_controle.png"},
    },
    "conhecimento": {"documentos": doc_list(), "hipoteses": descoberta.gerar_hipoteses(conn)},
    "campo": {"monitoramento": [monitoramento_ambiental.avaliar_municipio(m)
              for m in ["Cruz das Almas", "Governador Mangabeira", "Juazeiro"]]},
    "ia_aplicada": {
        "visao": [visao_computacional.classificar_imagem(n) for n in
                  ["folha_citros_001.jpg", "fruto_manga_044.jpg", "microscopia_fungo_007.png"]],
        "bioinfo": [{"id": cab[:28], **bioinformatica.estatisticas(seq)} for cab, seq in
                    bioinformatica.parse_fasta(">amostra_HLB_16S\nATGCGTACGTTAGCCGTAGCTAGGCTAGCTAGCTAGGCGCGCGTATATAT\n>controle\nATATATATATGCGCGCGCATATATGCGCGCATAT\n")],
    },
    "biotecnologia": {
        "indicadores": biotecnologia.indicadores(conn),
        "alertas": biotecnologia.alertas(conn, hoje="2026-06-04"),
        "culturas": [dict(c) for c in conn.execute(
            "SELECT lote,especie,estagio,n_mudas,contaminacao_pct FROM cultura_tecido").fetchall()],
        "matrizes": [dict(m) for m in conn.execute(
            "SELECT codigo,especie,status_sanitario,indexada_para FROM matriz_sadia").fetchall()],
    },
}
# limpa objetos Resultado (não serializáveis) da visão
for v in centro["ia_aplicada"]["visao"]:
    v.pop("resultado", None)

(PAINEL / "centro.json").write_text(json.dumps(centro, ensure_ascii=False, indent=2), encoding="utf-8")
conn.close()

inst = centro["instituto"]
print("Centro web gerado: painel/centro.json + painel/img/carta_controle.png")
print(f"  Instituto: {inst['projetos_ativos']} projetos ativos · {inst['pesquisadores']} pesquisadores · "
      f"{inst['publicacoes']} publicações")
print(f"  Laboratório: {len(centro['laboratorio']['equipamentos_alertas'])} alertas · QA/QC {centro['laboratorio']['qaqc']['status']}")
print(f"  Conhecimento: {len(centro['conhecimento']['documentos'])} documentos · {len(centro['conhecimento']['hipoteses'])} hipóteses")
print("\nVisualizar:  cd ../painel ; python -m http.server 8000 ; abra http://localhost:8000/centro.html")
