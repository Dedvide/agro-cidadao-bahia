/* SIPA-Bahia AI — dashboard multi-eixo (protótipo).
   KPIs ENAP + mapa (amostras / bolhas por município) + filtros + gráficos (Chart.js)
   + feed de recomendações. Resultados já vêm interpretados (rotulo, valor, classe, alerta). */

const COR_STATUS = { requer_atencao: "#c0392b", adequado: "#1b7a3d" };
const PALETA = ["#1b7a3d", "#2e86c1", "#e67e22", "#8e44ad", "#16a085", "#c0392b", "#f1c40f", "#7f8c8d"];
const ROTULO_EIXO = {
  fertilidade_solo: "Fertilidade do solo",
  analise_agua: "Qualidade da água",
  analise_foliar: "Análise foliar",
  residuos_agrotoxicos: "Resíduos de agrotóxicos",
  metais_pesados: "Metais pesados",
  qualidade_alimentos: "Qualidade de alimentos",
  diagnostico_molecular: "Diagnóstico molecular",
  monitoramento_pragas: "Monitoramento de pragas",
  fitopatologia: "Fitopatologia",
};
const nomeEixo = (c) => ROTULO_EIXO[c] || c;

let MAP, CAMADA, IND, GEO, BAHIA_MUN, BAHIA_UF;
const filtros = { categoria: "", status: "", camada: "bahia" };

async function carregar() {
  [IND, GEO] = await Promise.all([
    fetch("indicadores.json").then((r) => r.json()),
    fetch("amostras.geojson").then((r) => r.json()),
  ]);
  // malha real da Bahia (IBGE) — opcional; se faltar, o mapa cai para 'amostras'
  try {
    [BAHIA_MUN, BAHIA_UF] = await Promise.all([
      fetch("bahia-municipios.geojson").then((r) => r.json()),
      fetch("bahia-uf.geojson").then((r) => r.json()),
    ]);
  } catch (e) { BAHIA_MUN = BAHIA_UF = null; }
  montarKPIs(IND.indicadores_enap);
  montarCobertura(IND.cobertura);
  montarFiltro(IND);
  iniciarMapa();
  redesenhar();
  montarRecomendacoes(IND.recomendacoes);
  montarGraficos(IND);
  document.getElementById("revisao-info").textContent =
    `${IND.aguardando_revisao_humana} laudo(s) de baixa confiança aguardando ` +
    `revisão humana antes de entrar na base oficial.`;
}

function montarKPIs(e) {
  const cards = [
    { v: e.laudos_processados, r: "laudos processados" },
    { v: e.municipios_beneficiados, r: "municípios beneficiados" },
    { v: e.alertas_emitidos, r: "alertas emitidos", alerta: true },
    { v: e.pct_agricultura_familiar + "%", r: "agricultura familiar" },
    { v: e.taxa_alerta_pct + "%", r: "laudos com alerta", alerta: true },
    { v: "~" + e.tempo_estimado_economizado_h + "h", r: "tempo economizado (est.)" },
  ];
  document.getElementById("kpis").innerHTML = cards
    .map((c) => `<div class="card ${c.alerta ? "alerta" : ""}"><div class="valor">${c.v}</div>` +
      `<div class="rotulo">${c.r}</div></div>`)
    .join("");
}

const ROTULO_SOLIC = {
  agricultura_familiar: "Agric. familiar", produtor_rural: "Produtor rural",
  cooperativa: "Cooperativa", prefeitura: "Prefeitura", interno: "Interno", nao_informado: "N/I",
};

function montarCobertura(c) {
  if (!c) return;
  document.getElementById("cobertura").innerHTML =
    `<div class="cob-txt"><b>Cobertura do estado:</b> ${c.com_dados} de ${c.total_estado} municípios ` +
    `(${c.pct}%) — grande espaço para expandir o atendimento</div>` +
    `<div class="cob-bar"><div class="cob-fill" style="width:${Math.max(1.5, c.pct)}%"></div></div>`;
}

function montarFiltro(ind) {
  const sel = document.getElementById("filtro-categoria");
  ind.por_categoria.forEach(([cat]) => {
    const o = document.createElement("option");
    o.value = cat; o.textContent = nomeEixo(cat);
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => { filtros.categoria = sel.value; redesenhar(); });
  document.getElementById("filtro-status").addEventListener("change", (ev) => {
    filtros.status = ev.target.value; redesenhar();
  });
  document.querySelectorAll('input[name="camada"]').forEach((rb) =>
    rb.addEventListener("change", (ev) => { filtros.camada = ev.target.value; redesenhar(); })
  );
}

function iniciarMapa() {
  MAP = L.map("map").setView([-12.62, -39.05], 9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18, attribution: "© OpenStreetMap",
  }).addTo(MAP);
  legenda(MAP);
}

function featsFiltrados() {
  return GEO.features.filter((f) => {
    const p = f.properties;
    if (filtros.categoria && p.categoria_analise !== filtros.categoria) return false;
    if (filtros.status && p.status !== filtros.status) return false;
    return true;
  });
}

function redesenhar() {
  if (CAMADA) MAP.removeLayer(CAMADA);
  let modo = filtros.camada;
  if (modo === "bahia" && !BAHIA_MUN) modo = "amostras";
  CAMADA = modo === "bahia" ? camadaBahia()
         : modo === "municipios" ? camadaMunicipios()
         : camadaAmostras();
  CAMADA.addTo(MAP);
  const pad = modo === "bahia" ? 0.03 : 0.3;
  if (CAMADA.getBounds && CAMADA.getBounds().isValid()) MAP.fitBounds(CAMADA.getBounds().pad(pad));
  montarListaAtencao(featsFiltrados());
}

function estiloMun(p) {
  if (!p.tem_dados) return { fillColor: "#eef1f4", fillOpacity: 0.5, color: "#fff", weight: 0.5 };
  const fill = p.taxa_alerta >= 0.5 ? "#c0392b" : p.alertas > 0 ? "#e67e22" : "#1b7a3d";
  return { fillColor: fill, fillOpacity: 0.85, color: "#fff", weight: 0.6 };
}

function camadaBahia() {
  const grupo = L.featureGroup();
  L.geoJSON(BAHIA_MUN, {
    style: (f) => estiloMun(f.properties),
    onEachFeature: (f, layer) => {
      const p = f.properties;
      layer.bindTooltip(p.tem_dados
        ? `<b>${p.nome}</b><br>${p.n_laudos} laudo(s) · ${p.alertas} em alerta`
        : `<b>${p.nome}</b><br><span style="color:#999">sem dados ainda</span>`, { sticky: true });
    },
  }).addTo(grupo);
  if (BAHIA_UF) L.geoJSON(BAHIA_UF, { style: { color: "#0a3d62", weight: 2.5, fill: false } }).addTo(grupo);
  return grupo;
}

function camadaAmostras() {
  return L.geoJSON({ type: "FeatureCollection", features: featsFiltrados() }, {
    pointToLayer: (f, ll) => L.circleMarker(ll, {
      radius: 9, fillColor: COR_STATUS[f.properties.status] || "#5a6470",
      color: "#fff", weight: 2, fillOpacity: 0.9,
    }),
    onEachFeature: (f, layer) => layer.bindPopup(popupAmostra(f.properties)),
  });
}

function camadaMunicipios() {
  const grupo = L.featureGroup();
  IND.municipios.forEach((m) => {
    const taxa = m.total ? m.alertas / m.total : 0;
    const cor = taxa >= 0.5 ? "#c0392b" : taxa > 0 ? "#e67e22" : "#1b7a3d";
    L.circleMarker([m.lat, m.lon], {
      radius: 8 + m.total * 2.5, fillColor: cor, color: "#fff", weight: 2, fillOpacity: 0.75,
    })
      .bindPopup(`<div class="popup"><b>${m.nome}</b><br>${m.total} laudo(s) · ` +
        `${m.alertas} com alerta<br><small>taxa de alerta: ${Math.round(taxa * 100)}%</small></div>`)
      .addTo(grupo);
  });
  return grupo;
}

function corResultado(r) {
  if (r.alerta) return "#c0392b";
  if (r.classe && r.classe.toLowerCase().includes("medio")) return "#e67e22";
  return "#1b7a3d";
}

function popupAmostra(p) {
  const linhas = (p.resultados || []).map((r) => {
    const classe = r.classe
      ? `<span style="color:${corResultado(r)};font-weight:600">${r.classe}</span>` : "—";
    return `<tr><td>${r.rotulo}</td><td>${r.valor || "—"}</td><td>${classe}</td></tr>`;
  }).join("");
  const tag = p.status === "requer_atencao"
    ? '<span class="tag-atencao">requer atenção</span>'
    : '<span class="tag-ok">adequado</span>';
  return `<div class="popup"><b>Laudo ${p.laudo_id}</b> — ${tag}<br>` +
    `<small>${nomeEixo(p.categoria_analise)}</small><br>` +
    `${p.municipio} · ${p.tipo_amostra} · ${p.solicitante_tipo || ""}<br>` +
    `<small>coleta: ${p.data_coleta || "—"} · confiança: ${(p.confianca_geral ?? 0).toFixed(2)}</small>` +
    `<table>${linhas}</table></div>`;
}

function legenda(map) {
  const ctrl = L.control({ position: "bottomright" });
  ctrl.onAdd = () => {
    const div = L.DomUtil.create("div", "card");
    div.style.fontSize = "12px";
    div.innerHTML = `<b>Status</b><br>` +
      `<span style="color:${COR_STATUS.requer_atencao}">●</span> requer atenção<br>` +
      `<span style="color:${COR_STATUS.adequado}">●</span> adequado`;
    return div;
  };
  ctrl.addTo(map);
}

function montarRecomendacoes(recs) {
  document.getElementById("recomendacoes").innerHTML = (recs || []).slice(0, 12)
    .map((r) => `<li>${r.texto}<br><span class="meta">${r.laudo_id} · ${r.municipio} · ${nomeEixo(r.categoria)}</span></li>`)
    .join("") || "<li>Nenhuma recomendação.</li>";
}

function montarListaAtencao(feats) {
  const itens = feats.filter((f) => f.properties.status === "requer_atencao").map((f) => {
    const p = f.properties;
    const motivos = (p.resultados || []).filter((r) => r.alerta)
      .map((r) => `${r.rotulo} (${r.classe})`).join(", ");
    return `<li><b>${p.laudo_id}</b> · ${p.municipio}<br><small>${nomeEixo(p.categoria_analise)} — ${motivos}</small></li>`;
  }).join("");
  document.getElementById("lista-atencao").innerHTML =
    itens || "<li style='border-color:#1b7a3d;background:#e6f3ea;color:#1b7a3d'>Nenhuma amostra crítica no filtro.</li>";
}

function montarGraficos(ind) {
  const det = ind.por_categoria_detalhe;
  const labels = det.map((d) => nomeEixo(d.categoria));

  new Chart(document.getElementById("chart-eixos"), {
    type: "doughnut",
    data: { labels, datasets: [{ data: det.map((d) => d.total), backgroundColor: PALETA }] },
    options: { plugins: { legend: { position: "right", labels: { font: { size: 10 } } } } },
  });

  new Chart(document.getElementById("chart-alertas"), {
    type: "bar",
    data: { labels, datasets: [{ data: det.map((d) => d.alertas), backgroundColor: "#c0392b" }] },
    options: { indexAxis: "y", plugins: { legend: { display: false } },
      scales: { x: { ticks: { precision: 0 } } } },
  });

  new Chart(document.getElementById("chart-serie"), {
    type: "line",
    data: {
      labels: ind.serie_mensal.map(([m]) => m),
      datasets: [{ data: ind.serie_mensal.map(([, n]) => n), borderColor: "#1b7a3d",
        backgroundColor: "rgba(27,122,61,.15)", fill: true, tension: .3 }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { precision: 0 } } } },
  });

  // pH do solo (acidez) — cores por classe
  const CORES_PH = { "muito baixo (acido)": "#c0392b", baixo: "#e67e22", adequado: "#1b7a3d", alto: "#2e86c1" };
  const ph = ind.distribuicao_ph || [];
  new Chart(document.getElementById("chart-ph"), {
    type: "bar",
    data: { labels: ph.map(([c]) => c),
      datasets: [{ data: ph.map(([, n]) => n), backgroundColor: ph.map(([c]) => CORES_PH[c] || "#7f8c8d") }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { precision: 0 } } } },
  });

  // por tipo de solicitante
  const sol = ind.por_solicitante || [];
  new Chart(document.getElementById("chart-solicitante"), {
    type: "doughnut",
    data: { labels: sol.map(([t]) => ROTULO_SOLIC[t] || t),
      datasets: [{ data: sol.map(([, n]) => n), backgroundColor: PALETA }] },
    options: { plugins: { legend: { position: "right", labels: { font: { size: 10 } } } } },
  });

  // top municípios por nº de análises
  const rk = ind.ranking_municipios || [];
  new Chart(document.getElementById("chart-municipios"), {
    type: "bar",
    data: { labels: rk.map(([m]) => m),
      datasets: [{ data: rk.map(([, n]) => n), backgroundColor: "#1b7a3d" }] },
    options: { indexAxis: "y", plugins: { legend: { display: false } },
      scales: { x: { ticks: { precision: 0 } } } },
  });
}

carregar().catch((e) => {
  document.getElementById("kpis").innerHTML =
    `<div class="card" style="border-color:#c0392b">Erro ao carregar dados: ${e.message}.<br>` +
    `<small>Rode <code>python gerar_painel_demo.py</code> e sirva via <code>python -m http.server</code>.</small></div>`;
});
