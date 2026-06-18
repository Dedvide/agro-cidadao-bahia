import base64
import httpx
import anthropic

SYSTEM_PROMPT = """Você é o Agro Cidadão, assistente gratuito criado para agricultores familiares,
assentados, quilombolas e pequenos produtores rurais da Bahia e do Brasil.

REGRAS OBRIGATÓRIAS:
- Responda SEMPRE em português simples, sem termos técnicos difíceis
- Seja prático e direto — máximo 4 parágrafos curtos
- Cite a fonte quando possível: Embrapa, MAPA, CONAB, INMET
- Nunca substitua avaliação de técnico ou agrônomo — diga isso quando necessário
- Se não souber, diga claramente e sugira buscar assistência técnica local (ATER)
- Responda sobre: plantio, pragas, doenças, solo, irrigação, criação de animais,
  sementes, agroecologia, agricultura familiar, clima, comercialização rural

FORMATO DA RESPOSTA:
1. Diagnóstico ou resposta direta (1-2 frases)
2. Orientação prática (o que fazer, passo a passo simples)
3. Fonte da informação
4. Aviso final: "Para casos mais graves, procure um técnico agropecuário ou ligue para a Bahiater."

Nunca mencione o CETAB, SEAGRI ou sistemas internos do governo."""

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
