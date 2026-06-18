# Agro Cidadão Bahia — Plano-Mestre
### Programa Voluntário de Inclusão Tecnológica Rural com Inteligência Artificial
**Alvo:** Prêmio Servidor Cidadão — valorizaservidor.ba.gov.br
**Contato:** (71) 3115-1553 · valorizacaodoservidor@saeb.ba.gov.br
**Documento vivo · v1.0 · 2026-06-18**

---

## 0. Princípio que rege tudo

> A frase **"um servidor público dedicou seu tempo voluntariamente para levar ciência agropecuária a quem não pode pagar por ela"** precisa ser **verdadeira, comprovada e com beneficiários reais** no momento da inscrição.

O Prêmio Servidor Cidadão reconhece **ações voluntárias** — não sistemas institucionais. Este projeto existe fora das atribuições formais do cargo. O CETAB e a SEAGRI aparecem como **fonte de inspiração científica**, não como protagonistas.

---

## 1. O problema (a narrativa que abre a inscrição)

Um agricultor familiar no semiárido baiano acorda às cinco da manhã. Vai à lavoura. Encontra manchas estranhas nas folhas. Não tem agrônomo. Não tem assistência técnica constante. Não tem dinheiro para contratar consultoria.

Sua única alternativa é um grupo de WhatsApp, tentativa e erro, informação sem validação.

O resultado: perda de colheita, desperdício de insumo, insegurança alimentar, queda de renda.

**Isso acontece com a maioria dos pequenos produtores baianos.**

---

## 2. A solução: o "SUS do Conhecimento Agropecuário"

O SUS democratizou o acesso à saúde. O **Agro Cidadão Bahia** democratiza o acesso ao conhecimento técnico agropecuário.

Uma plataforma **gratuita**, acessível por **celular simples**, via **WhatsApp e navegador**, onde qualquer produtor rural pode:

- Tirar foto de uma planta e receber diagnóstico de praga ou doença
- Fazer perguntas em linguagem simples e receber orientação baseada em ciência
- Acessar cartilhas, manuais e microcursos gratuitos
- Conectar-se a uma rede de voluntários técnicos

Sem pagar. Sem sair da comunidade. Sem precisar entender termos técnicos.

---

## 3. Público beneficiado

- Agricultores familiares
- Assentamentos rurais
- Comunidades quilombolas
- Comunidades tradicionais
- Cooperativas e associações rurais
- Escolas agrícolas
- Jovens do campo
- Mulheres rurais

---

## 4. Os 5 módulos

### Módulo 1 — IA Rural (núcleo do projeto)
Assistente de texto que responde perguntas agropecuárias em linguagem simples.
Base de conhecimento: cartilhas e publicações públicas da Embrapa, MAPA, ZARC.
Acesso: portal web + WhatsApp.
**Status:** base técnica existente (`interpretar.py`, `repositorio.py`, `assistente.html`) — precisa ser desacoplada do CETAB e hospedada publicamente.

### Módulo 2 — Diagnóstico por Imagem
O agricultor fotografa folha, fruto ou solo. A IA sugere possíveis pragas, doenças ou deficiências nutricionais.
**Status:** stub existente (`visao_computacional.py`) — precisa ser implementado com API de visão (Claude Vision ou similar).

### Módulo 3 — Biblioteca Rural Digital
Cartilhas, vídeos e microcursos gratuitos organizados por tema:
hortaliças, fruticultura, apicultura, piscicultura, irrigação, agroecologia, comercialização.
**Status:** curadoria de conteúdo público Embrapa/MAPA — a construir.

### Módulo 4 — Mapa Solidário Rural
Rede de apoio conectando voluntários (estudantes, técnicos, pesquisadores) a produtores por região.
**Status:** base de mapa existente (`mapa.html`, GeoJSON) — desacoplar do CETAB e abrir ao público.

### Módulo 5 — Jovem Rural Digital
Capacitação tecnológica para jovens do campo:
IA aplicada ao agro, drones, agricultura digital, empreendedorismo rural.
**Status:** a construir (parceria com escolas agrícolas e universidades).

---

## 5. Base de conhecimento (independente do CETAB)

O projeto usa **exclusivamente fontes públicas** — sem dados internos do CETAB, sem laudos de clientes, sem sistemas governamentais privados.

| Fonte | O que oferece | Uso no projeto |
|---|---|---|
| **Embrapa** (publicações abertas + AgroAPI) | 40.000+ cartilhas, dados climáticos, NDVI | Base do M1 + M3 |
| **MAPA / AGROFIT** | Agrotóxicos registrados, normas, ZARC | Recomendações legais |
| **INMET** | Dados climáticos por município | Alertas e contexto climático |
| **IBGE / SIDRA** | Dados territoriais e produção agrícola | Mapa e indicadores |
| **CONAB** | Preços, safras, mercado | Orientação comercial |
| **Literatura científica aberta** | Artigos com DOI público | Fundamentação do M1 |

> O conhecimento científico acumulado em centros de pesquisa agropecuária da Bahia serviu de **inspiração** para a arquitetura do sistema — não como fonte de dados proprietária.

---

## 6. Por que é voluntário (critério central do edital)

O desenvolvimento deste projeto acontece **fora do horário de trabalho**, com recursos próprios (computador pessoal, hospedagem independente), sem uso de infraestrutura governamental (PRODEB, servidores da SEAGRI).

**Registro de horas voluntárias** — manter planilha com: data, horário, atividade desenvolvida, horas dedicadas. Este registro é a prova do "caráter voluntário" exigida pelo edital.

A hospedagem é independente — não PRODEB, não servidores do Estado.

---

## 7. O que torna o projeto único no Brasil

Existem iniciativas similares em partes — Embrapa digital, SENAR online, bots agrícolas privados. Nenhuma reúne simultaneamente:

| Componente | Existe isoladamente | Tudo junto |
|---|---|---|
| IA Generativa conversacional | Sim | **Não** |
| WhatsApp rural gratuito | Sim | **Não** |
| Diagnóstico por imagem | Sim | **Não** |
| Base em conhecimento científico público | Sim | **Não** |
| Foco exclusivo em agricultura familiar | Sim | **Não** |
| Capacitação gratuita integrada | Sim | **Não** |
| Rede de voluntários técnicos | Sim | **Não** |
| Iniciativa estadual cidadã | **Não** | **Não** |

**A inovação está na convergência**, não em cada componente isolado.

---

## 8. Indicadores de impacto (KPIs da inscrição)

O prêmio valoriza números reais. A estratégia é:

**Para a inscrição (o que já existe ou será construído antes do envio):**
- N° de agricultores atendidos (real — mesmo que pequeno: 10, 20, 50)
- N° de municípios alcançados
- N° de perguntas respondidas pela IA
- N° de horas voluntárias dedicadas

**Metas de expansão (para o formulário de "impacto esperado"):**

| Indicador | Meta Ano 1 | Meta Ano 2 |
|---|---|---|
| Pessoas atendidas | 500 | 5.000 |
| Municípios alcançados | 10 | 50 |
| Perguntas respondidas | 5.000 | 50.000 |
| Horas de capacitação | 200 | 2.000 |
| Jovens capacitados | 100 | 1.000 |

---

## 9. O que precisa ser feito antes de inscrever

### Obrigatório (sem isso não inscreve)
- [ ] Verificar prazo exato em `valorizaservidor.ba.gov.br`
- [ ] Confirmar elegibilidade: servidor ativo do Poder Executivo Estadual da Bahia
- [ ] Registrar horas voluntárias já dedicadas ao projeto

### Técnico (para ter algo funcionando)
- [ ] Adaptar `assistente.html` + backend para funcionar sem API do CETAB
- [ ] Criar base de conhecimento pública (cartilhas Embrapa em texto)
- [ ] Hospedar em URL pública independente (Render, Railway, Vercel ou similar — gratuito)
- [ ] Atender pelo menos 10 agricultores reais e documentar os atendimentos

### Para a inscrição
- [ ] Redigir texto de inscrição (seções: motivação, atividades, horas, beneficiários, impacto, envolvimento comunitário)
- [ ] Preparar evidências: capturas de tela, relatos de agricultores, planilha de horas voluntárias

---

## 10. Cronograma

```
JUN 2026 (agora)
  ├─ Verificar prazo de inscrição
  ├─ Adaptar assistente para funcionar sem CETAB
  ├─ Hospedar publicamente (URL acessível)
  └─ Iniciar registro de horas voluntárias

JUL 2026
  ├─ Piloto com agricultores reais (mínimo 10, 1 município)
  ├─ Documentar atendimentos e resultados
  └─ Redigir texto de inscrição

AGO 2026 (ou conforme prazo do edital)
  └─ Submeter inscrição em valorizaservidor.ba.gov.br

SET–DEZ 2026
  ├─ Expandir piloto (mais municípios, WhatsApp)
  ├─ Implementar M2 (diagnóstico por imagem)
  └─ Construir M3 (biblioteca rural)

2027
  ├─ Escala estadual
  ├─ M4 (Mapa Solidário) + M5 (Jovem Rural Digital)
  └─ Candidatura a outras premiações e políticas públicas
```

---

## 11. Texto de apoio para o formulário de inscrição

### Motivação para o trabalho voluntário
> Como servidor público da área agropecuária, observo diariamente a distância entre o conhecimento científico produzido pelas instituições de pesquisa e o agricultor familiar que mais precisa dele. Decidi usar minhas habilidades em tecnologia e inteligência artificial, voluntariamente e fora do horário de trabalho, para construir uma ponte entre esses dois mundos: um assistente gratuito, acessível por celular, que responde em linguagem simples as dúvidas de quem cultiva a terra.

### Atividades desenvolvidas
> Desenvolvimento voluntário de plataforma digital com inteligência artificial que permite a qualquer agricultor familiar, sem custo, tirar foto de uma planta doente e receber diagnóstico, fazer perguntas técnicas e receber orientação baseada em ciência, acessar cartilhas e microcursos gratuitos, e conectar-se a uma rede de voluntários técnicos. A plataforma usa conhecimento de fontes públicas (Embrapa, MAPA, literatura científica) e é hospedada independentemente, sem uso de recursos governamentais.

### Impacto comunitário
> O projeto elimina a barreira financeira e geográfica que impede o agricultor familiar de acessar orientação técnica qualificada. Um produtor em um pequeno município do semiárido, com um celular simples e sem internet de alta velocidade, passa a ter acesso ao mesmo nível de orientação científica disponível para grandes produtores que podem pagar agrônomos particulares. Isso reduz perdas de colheita, uso inadequado de insumos, insegurança alimentar e queda de renda nas comunidades rurais mais vulneráveis da Bahia.

---

## 12. Princípios não-negociáveis

- **Voluntário de verdade:** horas fora do trabalho, recursos próprios, hospedagem independente.
- **Gratuito para sempre:** o agricultor nunca paga nada, em nenhum módulo.
- **Ciência, não opinião:** toda resposta da IA cita a fonte (Embrapa, MAPA, literatura).
- **Linguagem simples:** output sempre em português acessível — sem jargão técnico.
- **Dados públicos apenas:** sem laudos, CRM ou dados internos do CETAB.
- **Números reais:** só divulgar métricas que existem de fato; não inflar.

---

## 13. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Comissão entender como projeto institucional | Enfatizar caráter voluntário + hospedagem independente + sem uso de dados do CETAB |
| Não ter beneficiários reais na inscrição | Fazer piloto mínimo (10 agricultores) antes de inscrever |
| Prazo de inscrição já encerrado | Verificar hoje em valorizaservidor.ba.gov.br; se encerrado, inscrever na próxima edição com projeto mais maduro |
| WhatsApp API bloqueado | Usar canal web para a inscrição; WhatsApp como expansão após a premiação |
| Manutenção do sistema sem recursos | Hospedar em tier gratuito (Render/Railway); conteúdo estático para a biblioteca |
| Conflito de interesse com cargo | Documentar que o desenvolvimento ocorre fora do expediente, sem uso de infra governamental |
