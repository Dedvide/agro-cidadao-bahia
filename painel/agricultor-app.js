/* Painel Digital do Agricultor — visão do produtor, consumindo a API (mesma origem). */

// município → bioma (10 municípios do projeto ABC+)
const BIOMA = {};
[["Caatinga", ["Juazeiro", "Casa Nova", "Irecê"]],
 ["Cerrado (Chapada Diamantina)", ["Palmeiras", "Mucugê", "Ibicoara", "Andaraí"]],
 ["Mata Atlântica", ["Tancredo Neves", "Itabuna", "Teixeira de Freitas"]],
].forEach(([b, ms]) => ms.forEach((m) => (BIOMA[m.toLowerCase()] = b)));

// recomendações ABC+ por bioma (Plano ABC+ Bahia)
const RECS = {
  "Caatinga": ["Recuperação de pastagens degradadas", "Sistemas irrigados sustentáveis",
    "Plantio direto", "Rotação de culturas", "Bioinsumos"],
  "Cerrado (Chapada Diamantina)": ["Recuperação de áreas degradadas", "Integração Lavoura-Pecuária-Floresta (ILPF)",
    "Sistemas irrigados sustentáveis", "Plantio direto", "Bioinsumos"],
  "Mata Atlântica": ["Sistemas Agroflorestais (SAFs) e cacau cabruca", "Recuperação de áreas degradadas",
    "Plantio direto", "Florestas plantadas", "Bioinsumos"],
};

let PROPS = [];

async function carregar() {
  try { PROPS = await fetch("/crm/propriedades").then((r) => r.json()); }
  catch (e) { document.getElementById("aviso-api").style.display = "block"; return; }
  const sel = document.getElementById("sel-prop");
  sel.innerHTML = PROPS.map((p) => `<option value="${p.id}">${p.nome} — ${p.municipio || ""}</option>`).join("");
  sel.addEventListener("change", () => mostrar(sel.value));
  if (PROPS.length) mostrar(PROPS[0].id);
}

async function mostrar(id) {
  const p = PROPS.find((x) => x.id == id);
  const bioma = BIOMA[(p.municipio || "").toLowerCase()] || "—";

  document.getElementById("prop").innerHTML = `
    <h2>🌱 Minha propriedade</h2>
    <div class="agri-big">${p.nome}</div>
    <div class="agri-meta">${p.municipio || ""} · ${bioma}</div>
    <div class="agri-meta">${p.area_ha || "—"} ha · cultura: ${p.cultura_principal || "—"}</div>`;

  // clima (API)
  try {
    const c = await fetch(`/clima/${encodeURIComponent(p.municipio)}`).then((r) => r.json());
    const cor = { alto: "#c0392b", medio: "#e67e22", baixo: "#1b7a3d", desconhecido: "#7f8c8d" }[c.risco.nivel];
    document.getElementById("clima").innerHTML = `
      <h2>🌦️ Clima e risco</h2>
      ${c.clima ? `<div class="agri-big">${c.clima.temp}°C · ${c.clima.umidade}% UR</div>` : "<div class='hint'>sem dado climático</div>"}
      <div class="pill" style="background:${cor}">risco fitossanitário ${c.risco.nivel}</div>
      <p class="agri-meta">${c.risco.motivo}</p>
      <p class="hint">fonte: monitoramento ambiental (INMET/SATVeg — APIs públicas)</p>`;
  } catch (e) { document.getElementById("clima").innerHTML = "<h2>🌦️ Clima</h2><p class='hint'>indisponível</p>"; }

  // laudos interpretados pela IA (do prontuário)
  const pr = await fetch(`/crm/propriedades/${id}/prontuario`).then((r) => r.json());
  const lab = (pr.analises_laboratoriais || []).map((a) =>
    `<li><b>${a.categoria_analise}</b> <span class="meta">${a.data_coleta || ""} · ${a.laudo_id}</span></li>`).join("");
  document.getElementById("laudos").innerHTML = `
    <h2>🔬 Meus laudos interpretados pela IA</h2>
    <ul class="lista">${lab || "<li>Sem análises ainda. Solicite uma coleta ao técnico.</li>"}</ul>
    <p class="hint">A IA transforma o resultado técnico em recomendação simples (ex.: pH baixo → calagem).</p>`;

  // recomendações ABC+
  const recs = (RECS[bioma] || []).map((r) => `<li>✅ ${r}</li>`).join("");
  document.getElementById("recs").innerHTML = `
    <h2>🌾 Recomendações ABC+ para você</h2>
    <ul class="lista">${recs || "<li>—</li>"}</ul>
    <p class="hint">práticas do Plano ABC+ Bahia para o bioma ${bioma}</p>`;

  // avisos do técnico (atendimentos pendentes + ocorrências)
  const avisos = [
    ...(pr.atendimentos || []).filter((a) => a.status !== "concluido").map((a) =>
      `<li class="alerta-item">📋 ${a.problema || "visita"} <span class="meta">— retorno ${a.retorno_previsto || "—"}</span></li>`),
    ...(pr.ocorrencias || []).map((o) => `<li class="alerta-item">🚨 ${o.tipo} ${o.descricao || ""}</li>`),
  ].join("");
  document.getElementById("avisos").innerHTML = `
    <h2>🔔 Avisos do técnico</h2><ul class="lista">${avisos || "<li>Nenhum aviso.</li>"}</ul>`;
}

carregar();
