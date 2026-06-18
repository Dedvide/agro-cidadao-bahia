# Fase 1 — Inventário do CETAB
### Preencha o que souber. Onde não souber, escreva "não sei" — isso também é informação.
*Este documento define a arquitetura real do sistema. Quanto mais preciso, melhor o MVP.*

---

## A. Identidade institucional (para o dossiê ENAP)

- **Nome oficial completo do CETAB:** _______
- **Vínculo (SEAGRI? autarquia? fundação?):** _______
- **Cidade/sede:** _______
- **A equipe que vai concorrer são servidores públicos em atividade?** (sim/não) _______
- **Quantas pessoas na equipe (2 a 20)?** _______
- **O CETAB já concorreu/foi premiado no Concurso de Inovação antes?** _______

---

## B. Quais análises o CETAB faz (o coração do escopo)

Liste os tipos de análise e, para cada um, o volume aproximado por mês:

| Tipo de análise | Ex. de amostra | Equipamento usado | Volume/mês | Quem é o cliente (produtor, município, interno…) |
|---|---|---|---|---|
| (ex.) Fertilidade de solo | solo | espectrômetro X | 200 | produtores rurais |
| (ex.) Resíduo de pesticida | fruta | HPLC/GC | ? | ? |
| (ex.) Diagnóstico molecular HLB | folha de citros | qPCR | ? | ? |
| ... | | | | |

> Dica: comece pelas 3 análises de **maior volume** — são as que mais geram dado e mais impacto.

---

## C. Como os dados existem hoje (define o extrator)

Para cada tipo de análise acima, responda:

1. **O resultado final fica em quê?** (Excel / Word / PDF / sistema próprio / papel)
2. **O layout é padronizado** entre técnicos e ao longo do tempo? (sim / mais ou menos / cada um faz do seu jeito)
3. **A máquina exporta** para CSV / Excel / formato aberto? Ou só PDF/impressão? Ou só formato proprietário?
4. **Onde os arquivos ficam guardados?** (pasta de rede, computador do técnico, e-mail, gaveta…)
5. **Há quantos anos de histórico** acumulado? Aproximadamente quantos arquivos/laudos no total?

| Análise | Formato do resultado | Padronizado? | Máquina exporta? | Onde fica guardado | Anos de histórico / nº arquivos |
|---|---|---|---|---|---|
| | | | | | |

---

## D. Equipamentos de laboratório (define formatos de exportação)

Liste as máquinas e, se souber, marca/modelo e software:

| Equipamento | Marca/modelo | Software | Exporta para formato aberto? (CSV/netCDF/mzML) |
|---|---|---|---|
| (ex.) Cromatógrafo gasoso | Agilent ... | ChemStation | netCDF? |
| (ex.) Termociclador qPCR | ... | ... | CSV de Ct? |
| ... | | | |

---

## E. Atendimento ao público (a narrativa de "bem público")

- **Quem solicita análises hoje?** (produtores, prefeituras, cooperativas, agricultura familiar…) _______
- **Como o resultado chega ao solicitante?** (papel, e-mail, retirada presencial…) _______
- **Quanto tempo leva** entre coleta e entrega do laudo, hoje? _______
- **O solicitante entende o laudo** ou precisa de um técnico para interpretar? _______
- **Há gargalo/fila?** Qual? _______

---

## F. Infraestrutura disponível (define o que dá para implantar)

- **O CETAB/SEAGRI tem servidores próprios? Nuvem? Qual?** _______
- **Há equipe de TI?** _______
- **Há restrição de orçamento / precisa ser custo zero?** _______
- **Há política de dados/LGPD já adotada pelo órgão?** _______

---

## G. O que o CETAB já faz que se PARECE com inovação/IA (para a narrativa honesta)

- **Já usam alguma automação, script, planilha inteligente, sistema próprio?** Descreva. _______
- **Já cruzam dados de análises para tomar decisão?** (ex.: mapa de incidência de praga) _______
- **Já houve projeto/pesquisa premiado?** (ex.: mel de cacau 2025) _______

---

## Quando terminar
Salve este arquivo e me avise. Com ele + o estudo de pesquisa, entrego:
1. Diagnóstico do estado atual
2. Esquema canônico de dados (a estrutura da base única)
3. Recomendação de escopo do MVP (quais 2-3 análises atacar primeiro)
