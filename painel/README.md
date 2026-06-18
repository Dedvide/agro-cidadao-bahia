# Painel de Indicadores — SIPA-Bahia AI (protótipo)

Dashboard web estático (HTML + Leaflet) que visualiza o Data Lake:
**mapa georreferenciado das amostras + cards de indicadores + fila de revisão**.
É o embrião do "Mapa Inteligente da Bahia" e ótimo material visual para o pitch da ENAP.

## Como ver

```powershell
# 1. gerar os dados (a partir do Data Lake) — roda SEM API
cd ..\prototipo-extrator
python gerar_painel_demo.py

# 2. servir o painel (fetch precisa de http, não file://)
cd ..\painel
python -m http.server 8000
# abra http://localhost:8000
```

## O que aparece

- **Cards**: laudos processados, municípios cobertos, solos com fósforo baixo, aguardando revisão.
- **Mapa**: cada amostra é um ponto — vermelho = requer atenção, verde = adequado.
  Clique para ver o laudo interpretado (analito, valor, classe).
- **Painel lateral**: amostras críticas, distribuição de fósforo, trilha de auditoria.

## Arquivos

| Arquivo | Papel |
|---|---|
| `index.html` / `style.css` / `app.js` | O dashboard |
| `amostras.geojson` | Pontos (gerado por `gerar_painel_demo.py`) |
| `indicadores.json` | Cards/indicadores (idem) |

## Protótipo → produção

| Hoje | Produção |
|---|---|
| HTML estático + Leaflet | Next.js + React (stack do plano) |
| GeoJSON de arquivo | API FastAPI sobre PostGIS |
| Dados de demonstração | Laudos reais do CETAB |
| Pontos por centroide de município | Coordenada real + camadas (solo, água, pragas) |
