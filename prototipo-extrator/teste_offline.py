"""Teste offline (sem API): valida esquema + interpretação com um Laudo manual."""
from schema import Laudo, Resultado, TipoAmostra, TipoSolicitante
from interpretar import interpretar_laudo

# Simula o que o extrator IA devolveria para o laudo_solo_01.txt
laudo = Laudo(
    laudo_id="2026/0457",
    categoria_analise="fertilidade_solo",
    tipo_amostra=TipoAmostra.solo,
    data_coleta="2026-03-12",
    data_analise="2026-03-20",
    solicitante_nome="Joao Pereira dos Santos",
    solicitante_tipo=TipoSolicitante.agricultura_familiar,
    municipio="Cruz das Almas",
    propriedade="Sitio Boa Esperanca",
    laboratorio="CETAB - Lab. de Solos",
    resultados=[
        Resultado(analito="ph", valor=5.2, metodo="agua"),
        Resultado(analito="fosforo", valor=8.0, unidade="mg/dm3", metodo="Mehlich-1"),
        Resultado(analito="potassio", valor=35.0, unidade="mg/dm3"),
        Resultado(analito="calcio", valor=2.1, unidade="cmolc/dm3"),
        Resultado(analito="magnesio", valor=0.8, unidade="cmolc/dm3"),
        Resultado(analito="materia_organica", valor=1.4, unidade="%"),
    ],
    confianca_geral=0.95,
)

print("Validacao Pydantic: OK")
print(f"Laudo {laudo.laudo_id} | {laudo.municipio} | {laudo.solicitante_tipo.value}")
print("-" * 64)
for it in interpretar_laudo(laudo):
    flag = "!" if it.alerta else " "
    rec = f" -> {it.recomendacao}" if it.recomendacao else ""
    print(f" {flag} {it.rotulo:18} {it.valor_exibicao:14} [{it.classe or '-'}]{rec}")
print("-" * 64)
print("Engrenagem de interpretacao: OK")
