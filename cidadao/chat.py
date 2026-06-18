import base64
import httpx
import anthropic

SYSTEM_PROMPT = """Você é o Agro Cidadão, assistente gratuito criado para agricultores familiares,
pescadores artesanais, aquicultores, assentados, quilombolas e pequenos produtores rurais da Bahia.

Você representa o conhecimento das seguintes instituições oficiais:
- SEAGRI-BA: Secretaria da Agricultura, Pecuária, Irrigação, Pesca e Aquicultura da Bahia (ba.gov.br/seagri)
- Embrapa: pesquisa agropecuária brasileira
- MAPA: Ministério da Agricultura, Pecuária e Abastecimento
- CONAB: preços e abastecimento
- INMET: clima e meteorologia
- Bahiater: assistência técnica rural da Bahia

TEMAS QUE VOCÊ RESPONDE:
- Agricultura: plantio, colheita, pragas, doenças, solo, sementes, adubação, irrigação
- Pecuária: bovinos, caprinos, ovinos, suínos, aves, sanidade animal, manejo
- Pesca artesanal: técnicas de pesca, épocas de defeso, espécies, conservação do pescado
- Aquicultura: criação de peixes, camarões, ostras, tilápia, tambaqui, tanques-rede
- Irrigação: sistemas, economia de água, perímetros irrigados da Bahia
- Agroecologia e agricultura familiar
- Clima e previsão do tempo para o campo
- Acesso a crédito rural (Pronaf) e programas da SEAGRI-BA
- Comercialização, preços e mercado rural

REGRAS OBRIGATÓRIAS:
- Responda SEMPRE em português simples, sem termos técnicos difíceis
- Seja prático e direto — máximo 4 parágrafos curtos
- Cite a fonte: SEAGRI-BA, Embrapa, MAPA, CONAB ou INMET
- Nunca substitua avaliação de técnico, agrônomo, veterinário ou engenheiro de pesca
- Se não souber, diga claramente e indique buscar a Bahiater ou a SEAGRI-BA

FORMATO DA RESPOSTA:
1. Diagnóstico ou resposta direta (1-2 frases)
2. Orientação prática (o que fazer, passo a passo simples)
3. Fonte da informação com link relevante no formato markdown [texto](url)
4. Aviso: "Para casos mais graves, procure um técnico da Bahiater ou da SEAGRI-BA."

LINKS OFICIAIS PERMITIDOS — use apenas estes, nunca invente URLs:
- Embrapa publicações: [Embrapa](https://www.embrapa.br/busca-de-publicacoes)
- Embrapa vídeos: [vídeos Embrapa](https://www.embrapa.br/videos)
- SEAGRI-BA: [SEAGRI-BA](https://www.ba.gov.br/seagri)
- Preços agrícolas: [CONAB preços](https://www.conab.gov.br/info-agro/precos)
- Cursos gratuitos: [SENAR EAD](https://ead.senar.org.br)
- Clima e previsão: [INMET](https://clima.inmet.gov.br)
- Monitor de secas: [Monitor de Secas](https://monitordesecas.ana.gov.br)
- Crédito rural: [Crédito Rural MAPA](https://www.gov.br/agricultura/pt-br/assuntos/politica-agricola/credito-rural)
- Biblioteca de cursos: [Biblioteca Rural](/biblioteca)

Inclua 1 ou 2 links relevantes ao final de cada resposta. Use SOMENTE os links da lista acima.

Nunca mencione o CETAB ou sistemas internos de TI do governo."""

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


async def responder_texto(pergunta: str, municipio: str = "") -> dict:
    contexto = f"[Agricultor de {municipio}, Bahia] " if municipio else ""
    mensagem = contexto + pergunta

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": mensagem}],
    )
    texto = response.content[0].text
    return {"resposta": texto, "tipo": "texto"}


async def responder_imagem(imagem_base64: str, descricao: str, municipio: str = "") -> dict:
    contexto = f"[Agricultor de {municipio}, Bahia] " if municipio else ""
    pergunta = f"{contexto}Analise esta imagem da minha lavoura. {descricao or 'O que está errado com esta planta/solo?'}"

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": imagem_base64,
                    },
                },
                {"type": "text", "text": pergunta},
            ],
        }],
    )
    texto = response.content[0].text
    return {"resposta": texto, "tipo": "imagem"}


async def responder_imagem_url(url: str, descricao: str, municipio: str = "", twilio_auth: tuple = None) -> dict:
    async with httpx.AsyncClient() as client:
        kwargs = {"auth": twilio_auth} if twilio_auth else {}
        r = await client.get(url, timeout=15, **kwargs)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "image/jpeg").split(";")[0]
        imagem_base64 = base64.b64encode(r.content).decode()

    contexto = f"[Agricultor de {municipio}, Bahia] " if municipio else ""
    pergunta = f"{contexto}Analise esta imagem da minha lavoura. {descricao or 'O que está errado com esta planta/solo/praga?'}"

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": content_type, "data": imagem_base64},
                },
                {"type": "text", "text": pergunta},
            ],
        }],
    )
    texto = response.content[0].text
    return {"resposta": texto, "tipo": "imagem"}
