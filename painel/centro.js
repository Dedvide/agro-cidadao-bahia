/* Centro de Pesquisa — visão integrada dos módulos (leitura de centro.json). */
let DADOS;

async function carregar() {
  DADOS = await fetch("centro.json").then((r) => r.json());
  kpis(DADOS.instituto);
  pesquisa(DADOS.pesquisa);
  laboratorio(DADOS.laboratorio);
  conhecimento(DADOS.conhecimento);
  campo(DADOS.campo);
  visao(DADOS.ia_aplicada.visao);
  bioinfo(DADOS.ia_aplicada.bioinfo);
  biotec(DADOS.biotecnologia);
}

function kpis(i) {
  const b = i.bibliometria || {};
  const cards = [
    { v: i.projetos_ativos, t: "projetos ativos" },
    { v: i.pesquisadores, t: "pesquisadores" },
    { v: i.bolsas_ativas, t: "bolsas ativas" },
    { v: i.publicacoes, t: "publicações (projetos)" },
    { v: b.total || 0, t: "publicações (DOI)" },
    { v: "R$ " + ((i.investimento_editais || 0) / 1000) + "k", t: "editais" },
  ];
  document.getElementById("kpis").innerHTML = cards.map((c) =>
    `<div class="card"><div class="valor">${c.v}</div><div class="rotulo">${c.t}</div></div>`).join("");
}

function pesquisa(p) {
  const proj = p.projetos.map((x) =>
    `<li><b>${x.titulo}</b> <span class="pill ${x.status}">${x.status}</span>
       <span class="meta">${x.financiador || ""}</span></li>`).join("");
  const pes = p.pesquisadores.map((x) =>
    `<li>${x.nome} <span class="meta">${x.area || ""}${x.orcid ? " · ORCID " + x.orcid : ""}</span></li>`).join("");
  document.getElementById("pesquisa").innerHTML =
    `<h3>Projetos</h3><ul class="lista">${proj}</ul><h3>Pesquisadores</h3><ul class="lista">${pes}</ul>`;
}

function laboratorio(l) {
  const alertas = l.equipamentos_alertas.map((a) =>
    `<li class="alerta-item"><b>${a.tipo.replace(/_/g, " ")}</b>: ${a.item} <span class="meta">${a.detalhe}</span></li>`).join("");
  const q = l.qaqc;
  const viol = (q.violacoes || []).map((v) => `<li>${v[0]}: ${v[1]}</li>`).join("");
  document.getElementById("laboratorio").innerHTML = `
    <h3>Pendências de equipamentos/reagentes</h3>
    <ul class="lista">${alertas || "<li>nenhuma</li>"}</ul>
    <h3>QA/QC analítico — <span class="${q.status === "sob controle" ? "ok" : "ruim"}">${q.status}</span></h3>
    <ul class="lista">${viol}</ul>
    <img class="grafico-img" src="${q.grafico}" alt="carta de controle" />`;
}

function conhecimento(c) {
  renderDocs(c.documentos);
  document.getElementById("busca").addEventListener("input", (e) => {
    const t = e.target.value.toLowerCase().trim();
    const filt = !t ? c.documentos : c.documentos.filter((d) =>
      (d.titulo + " " + (d.texto || "")).toLowerCase().includes(t));
    renderDocs(filt);
  });
  document.getElementById("hipoteses").innerHTML = c.hipoteses.map((h) => `<li>${h}</li>`).join("");
}

function renderDocs(docs) {
  document.getElementById("docs").innerHTML = docs.map((d) =>
    `<div class="doc"><span class="pill tipo">${d.tipo}</span> <b>${d.titulo}</b>
       <span class="meta">${d.ano || ""}${d.doi ? " · DOI " + d.doi : ""}</span></div>`).join("")
    || "<p class='meta'>nenhum documento encontrado.</p>";
}

function campo(c) {
  document.getElementById("campo").innerHTML = c.monitoramento.map((m) => {
    const cl = m.clima ? `${m.clima.temp}°C · ${m.clima.umidade}% UR` : "sem dado";
    const cor = { alto: "#c0392b", medio: "#e67e22", baixo: "#1b7a3d", desconhecido: "#7f8c8d" }[m.risco.nivel];
    return `<div class="linha-campo"><b>${m.municipio}</b> <span class="meta">${cl}</span>
       <span class="pill" style="background:${cor}">risco ${m.risco.nivel}</span>
       <div class="meta">${m.risco.motivo}</div></div>`;
  }).join("");
}

function visao(v) {
  document.getElementById("visao").innerHTML = v.map((x) => {
    const cor = x.resultado_diagnostico === "negativo" ? "#1b7a3d" : "#c0392b";
    return `<div class="linha-campo">📷 <b>${x.arquivo}</b> →
       <span style="color:${cor};font-weight:600">${x.classe}</span>
       <span class="meta">${Math.round(x.confianca * 100)}% confiança</span></div>`;
  }).join("") + "<p class='meta'>placeholder — produção: YOLO/ViT/SAM treinados</p>";
}

function bioinfo(b) {
  document.getElementById("bioinfo").innerHTML = b.map((s) =>
    `<div class="linha-campo">🧬 <b>${s.id}</b> <span class="meta">len ${s.comprimento} · GC ${s.gc_percent}%</span></div>`).join("")
    + "<p class='meta'>parser FASTA real; BLAST/Nextflow são stubs</p>";
}

function biotec(b) {
  const ind = b.indicadores;
  const kpis = `<div class="biotec-kpis">
    <span><b>${ind.mudas_em_producao}</b> mudas</span>
    <span><b>${ind.lotes_bioproduto}</b> bioprodutos</span>
    <span><b>${ind.acessos_germoplasma}</b> germoplasma</span>
    <span><b>${ind.matrizes_sadias}</b> matrizes sadias</span></div>`;
  const culturas = b.culturas.map((c) => {
    const cor = c.contaminacao_pct > 10 ? "#c0392b" : "#1b7a3d";
    return `<div class="linha-campo">🌱 <b>${c.lote}</b> ${c.especie} <span class="meta">${c.estagio} · ${c.n_mudas} mudas</span>
       <span style="color:${cor};font-weight:600">contam. ${c.contaminacao_pct}%</span></div>`;
  }).join("");
  const matrizes = b.matrizes.map((m) => {
    const ok = (m.status_sanitario || "").toLowerCase() === "sadia";
    return `<div class="linha-campo">🍃 <b>${m.codigo}</b> ${m.especie}
       <span style="color:${ok ? "#1b7a3d" : "#c0392b"};font-weight:600">${m.status_sanitario}</span>
       <span class="meta">indexada p/ ${m.indexada_para}</span></div>`;
  }).join("");
  const alertas = b.alertas.map((a) =>
    `<li class="alerta-item"><b>${a.tipo.replace(/_/g, " ")}</b>: ${a.item} <span class="meta">${a.detalhe}</span></li>`).join("");
  document.getElementById("biotec").innerHTML =
    kpis + "<h3>Cultura de tecidos</h3>" + culturas +
    "<h3>Matrizes sadias (limpeza clonal)</h3>" + matrizes +
    "<h3>Alertas de QC</h3><ul class='lista'>" + (alertas || "<li>nenhum</li>") + "</ul>";
}

carregar().catch((e) => {
  document.getElementById("kpis").innerHTML =
    `<div class="card" style="border-color:#c0392b">Erro: ${e.message}.<br>` +
    `<small>Rode <code>python gerar_centro_web.py</code> e sirva via <code>python -m http.server</code>.</small></div>`;
});
