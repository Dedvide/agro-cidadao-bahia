/* Portal Operacional (CRM) — consome a API ao vivo (mesma origem quando servido por /app). */

const API = ""; // mesma origem (FastAPI serve /app e os endpoints /crm/*)

async function get(rota) {
  const r = await fetch(API + rota);
  if (!r.ok) throw new Error(rota + " → " + r.status);
  return r.json();
}
async function post(rota, corpo) {
  const r = await fetch(API + rota, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo),
  });
  if (!r.ok) throw new Error(rota + " → " + r.status);
  return r.json();
}

let PRODUTORES = [], PROPRIEDADES = [];

async function carregar() {
  try {
    [PRODUTORES, PROPRIEDADES] = await Promise.all([get("/crm/produtores"), get("/crm/propriedades")]);
    preencherSelects();
    document.getElementById("v-data").valueAsDate = new Date();
  } catch (e) {
    document.getElementById("aviso-api").style.display = "block";
  }
}

function preencherSelects() {
  const opP = PROPRIEDADES.map((p) => `<option value="${p.id}">${p.nome} — ${p.municipio || ""}</option>`).join("");
  document.getElementById("v-prop").innerHTML = opP;
  document.getElementById("pr-sel").innerHTML = `<option value="">selecione...</option>` + opP;
  document.getElementById("i-prod").innerHTML =
    PRODUTORES.map((p) => `<option value="${p.id}">${p.nome}</option>`).join("");
}

// ── registrar visita (o ato operacional central) ──
document.getElementById("form-visita").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("v-msg");
  try {
    await post("/crm/atendimentos", {
      propriedade_id: +document.getElementById("v-prop").value,
      tecnico: document.getElementById("v-tec").value,
      data: document.getElementById("v-data").value,
      tipo: document.getElementById("v-tipo").value,
      problema: document.getElementById("v-prob").value || null,
      orientacao: document.getElementById("v-orient").value || null,
      retorno_previsto: document.getElementById("v-ret").value || null,
      status: "aberto",
    });
    msg.textContent = "✓ visita registrada"; msg.className = "form-msg ok";
    document.getElementById("v-prob").value = ""; document.getElementById("v-orient").value = "";
    if (document.getElementById("pr-sel").value == document.getElementById("v-prop").value)
      verProntuario(document.getElementById("v-prop").value);
  } catch (err) { msg.textContent = "✗ " + err.message; msg.className = "form-msg ruim"; }
});

// ── cadastros rápidos ──
document.getElementById("form-prod").addEventListener("submit", async (e) => {
  e.preventDefault();
  await post("/crm/produtores", {
    documento: document.getElementById("p-doc").value, nome: document.getElementById("p-nome").value,
    municipio: document.getElementById("p-mun").value || null, telefone: document.getElementById("p-tel").value || null,
  });
  e.target.reset(); PRODUTORES = await get("/crm/produtores"); preencherSelects();
});
document.getElementById("form-imovel").addEventListener("submit", async (e) => {
  e.preventDefault();
  await post("/crm/propriedades", {
    nome: document.getElementById("i-nome").value, produtor_id: +document.getElementById("i-prod").value,
    municipio: document.getElementById("i-mun").value || null, cultura_principal: document.getElementById("i-cult").value || null,
  });
  e.target.reset(); PROPRIEDADES = await get("/crm/propriedades"); preencherSelects();
});

// ── prontuário ──
document.getElementById("pr-sel").addEventListener("change", (e) => { if (e.target.value) verProntuario(e.target.value); });

async function verProntuario(id) {
  const d = await get(`/crm/propriedades/${id}/prontuario`);
  const atend = d.atendimentos.map((a) => `
    <li class="${a.status === "concluido" ? "" : "alerta-item"}">
      <b>${a.data}</b> · ${a.tipo} <span class="meta">(${a.tecnico})</span><br>
      ${a.problema ? "⚠ " + a.problema : ""} ${a.orientacao ? "→ " + a.orientacao : ""}
      <span class="meta">${a.status}${a.retorno_previsto ? " · retorno " + a.retorno_previsto : ""}</span></li>`).join("");
  const ocor = d.ocorrencias.map((o) => `<li class="alerta-item"><b>${o.tipo}</b> ${o.descricao || ""} <span class="meta">[${o.status}]</span></li>`).join("");
  const lab = d.analises_laboratoriais.map((a) => `<li>${a.data_coleta} · ${a.categoria_analise} <span class="meta">${a.laudo_id}</span></li>`).join("");
  document.getElementById("prontuario").innerHTML = `
    <div class="pront-cab"><b>${d.propriedade.nome}</b> · ${d.propriedade.municipio || ""}
      <span class="meta">${d.produtor ? "produtor: " + d.produtor.nome : ""}</span></div>
    <h3>Atendimentos (${d.atendimentos.length})</h3><ul class="lista">${atend || "<li>—</li>"}</ul>
    <h3>Ocorrências (${d.ocorrencias.length})</h3><ul class="lista">${ocor || "<li>—</li>"}</ul>
    <h3>Análises laboratoriais (${d.analises_laboratoriais.length})</h3><ul class="lista">${lab || "<li>sem análises no município</li>"}</ul>`;
}

// ── carteira do técnico ──
document.getElementById("c-btn").addEventListener("click", verCarteira);
async function verCarteira() {
  const tec = document.getElementById("c-tec").value;
  const c = await get(`/crm/tecnicos/${encodeURIComponent(tec)}/carteira`);
  const ret = (c.proximos_retornos || []).map((r) =>
    `<li><b>${r.retorno_previsto}</b> ${r.problema || ""}</li>`).join("");
  document.getElementById("carteira").innerHTML = `
    <div class="biotec-kpis">
      <span><b>${c.propriedades_atendidas}</b> propriedades</span>
      <span><b>${c.visitas_realizadas}</b> visitas</span>
      <span><b>${c.municipios.length}</b> municípios</span>
      <span><b>${c.pendencias}</b> pendências</span>
    </div>
    <h3>Próximos retornos</h3><ul class="lista">${ret || "<li>nenhum</li>"}</ul>`;
}

carregar();
