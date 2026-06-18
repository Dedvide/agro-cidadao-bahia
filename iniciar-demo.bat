@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0prototipo-extrator"

echo.
echo  ============================================================
echo   SIPA-Bahia AI - preparando a demonstracao
echo  ============================================================
echo.
echo  [0/6] Verificando dependencias (so na primeira vez demora)...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo.
echo  [1/6] Telas de laudo IA / assistente (dados de demo)...
python gerar_demo_secretario.py
echo  [2/6] Dados ABC+/PRODEAGRO (10 municipios, 3 biomas) + mapa + indicadores...
python gerar_abc.py
echo  [3/6] LIMS...
python gerar_lims_demo.py
echo  [4/6] Centro de Pesquisa...
python gerar_centro_web.py
echo  [5/6] Ontologia / Ficha 360...
cd /d "%~dp0"
python -m ontology.materializar
echo  [6/6] API (backend) + CRM ABC+ (propriedades nos 10 municipios)...
cd /d "%~dp0api"
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
python crm_seed.py
echo  Subindo servidor unificado (painel + API + CRM)...

echo.
echo  ============================================================
echo   Interface operacional:  http://127.0.0.1:8001/app/
echo   Documentacao da API:    http://127.0.0.1:8001/docs
echo   Deixe ESTA JANELA ABERTA.
echo  ============================================================
echo.
start "" http://127.0.0.1:8001/app/
python -m uvicorn main:app --host 127.0.0.1 --port 8001
