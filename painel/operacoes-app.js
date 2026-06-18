/* Centro de Operações — consome /operacoes/resumo ao vivo, com auto-refresh. */

function relogio() {
  document.getElementById("relogio").textContent = new Date().toLocaleString("pt-BR");
}
setInterval(relogio, 1000); relogio();

async function carregar() {
  let d;
  try { d = await fetch("/operacoes/resumo").then((r) => r.json()); }
  catch (e) {
    document.getElementById("erro").style.display = "block";
    document.getElementById("erro").textContent = "API indisponível — suba: cd api ; uvicorn main:app --port 8001";
    return;
  }
  document.getElementById("erro").style.display = "none";
  kpis(d.kpis);
  focos(d.focos_sanitarios);
  alertas(d.alertas_recentes);
  pendencias(d.pendencias);
  metas(d.metas);
  bioma(d.propriedades_por_bioma);
}

function kpis(k) {
  const tiles = [
    { v: k.laudos, r: "laudos", c: "" },
    { v: k.propriedades, r: "propriedades", c: "ok" },
    { v: k.municipios, r: "municípios", c: "" },
    { v: k.focos, r: "focos sanitários", c: k.focos ? "crit" : "ok" },
    { v: k.alertas, r: "alertas", c: k.alertas ? "warn" : "ok" },
    { v: k.pendencias, r: "pendências", c: k.pendencias ? "warn" : "ok" },
  ];
  document.getElementById("kpis").innerHTML = tiles.map((t) =>
    `<div class="ops-kpi ${t.c}"><div class="v">${t.v}</div><div class="r">${t.r}</div></div>`).join("");
}

function focos(f) {
  document.getElementById("focos").innerHTML = f.length ? f.map((x) =>
    `<div class="ops-item"><span class="tag-foco">${(x.alvo || "").toUpperCase()}</span> em <b>${x.municipio}</b>
       <div class="meta">notificar defesa agropecuária (ADAB)</div></div>`).join("")
    : "<div class='ops-item meta'>nenhum foco ativo</div>";
}

function alertas(a) {
  document.getElementById("alertas").innerHTML = a.length ? a.map((x) =>
    `<div class="ops-item">${x.rotulo} <b>[${x.classe}]</b> <span class="meta">· ${x.municipio}</span></div>`).join("")
    : "<div class='ops-item meta'>sem alertas</div>";
}

function pendencias(p) {
  document.getElementById("pendencias").innerHTML = p.length ? p.map((x) =>
    `<div class="ops-item">${x.problema || "visita"} <span class="meta">· ${x.tecnico || ""} · retorno ${x.retorno_previsto || "—"}</span></div>`).join("")
    : "<div class='ops-item meta'>nenhuma pendência</div>";
}

function metas(m) {
  const cor = (p) => (p >= 100 ? "#2ecc71" : p >= 50 ? "#3498db" : p >= 20 ? "#e67e22" : "#e74c3c");
  document.getElementById("metas").innerHTML = m.slice(0, 5).map((x) => {
    const w = Math.min(100, x.pct);
    return `<div class="ops-bar-linha"><span class="nome">${x.meta}</span>
      <span class="ops-bar"><div style="width:${w}%;background:${cor(x.pct)}"></div></span>
      <span class="num">${x.atual}/${x.alvo}</span></div>`;
  }).join("");
}

function bioma(b) {
  document.getElementById("bioma").innerHTML =
    `<div class="bioma-tiles">` + Object.entries(b).map(([nome, n]) =>
      `<div class="bioma-tile"><b>${n}</b><span>${nome}</span></div>`).join("") + `</div>`;
}

carregar();
setInterval(carregar, 30000); // auto-refresh 30s
