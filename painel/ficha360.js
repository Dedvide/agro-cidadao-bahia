/* Ficha 360 do Município — lê painel/ontologia.json (materializada do SIPA via Data Fabric). */
let O;

async function carregar() {
  O = await fetch("ontologia.json").then((r) => r.json());
  kpis(O.resumo);
  linhagem(O.lineage);
  seletor(O.municipios);
  const primeiro = O.municipios[0];
  if (primeiro) mostrar(primeiro.ibge_code);
}

function kpis(r) {
  const cards = [
    { v: r.municipios, t: "municípios na ontologia" },
    { v: r.analises, t: "análises vinculadas" },
    { v: r.eventos, t: "eventos sanitários" },
    { v: r.entidades, t: "entidades totais" },
  ];
  document.getElementById("kpis").innerHTML = cards.map((c) =>
    `<div class="card"><div class="valor">${c.v}</div><div class="rotulo">${c.t}</div></div>`).join("");
}

function linhagem(l) {
  const total = l.reduce((s, x) => s + x.n, 0) || 1;
  document.getElementById("lineage-list").innerHTML = l.map((x) => {
    const w = Math.max(6, (x.n / total) * 200);
    return `<div class="barra-linha"><span class="nome">${x.origin_system}</span>
      <span class="barra" style="width:${w}px;background:#2e86c1"></span><span class="num">${x.n}</span></div>`;
  }).join("");
}

function seletor(municipios) {
  const sel = document.getElementById("sel-municipio");
  sel.innerHTML = municipios.map((m) =>
    `<option value="${m.ibge_code}">${m.name} — ${m.region || ""}</option>`).join("");
  sel.addEventListener("change", () => mostrar(sel.value));
}

function mostrar(ibge) {
  const f = O.fichas[ibge];
  if (!f) return;
  const m = f.municipio;
  const analises = f.analises.map((a) => {
    const res = Object.entries(a.result || {}).map(([k, v]) => `${k}: ${v}`).join(" · ");
    return `<tr><td>${a.analysis_type}</td><td>${a.collected_at || "—"}</td>
      <td>${res || "—"}</td><td><span class="pill tipo">${a.origin_system}</span></td></tr>`;
  }).join("");
  const eventos = f.eventos.map((e) =>
    `<li class="alerta-item"><b>${e.event_type}</b> <span class="meta">[${e.status}] · ${e.occurred_at} · ${e.origin_system}</span></li>`).join("");

  document.getElementById("ficha").innerHTML = `
    <div class="ficha-cab">
      <h2>${m.name} <span class="pill">IBGE ${m.ibge_code}</span></h2>
      <div class="meta">Região: ${m.region || "—"} · ${f.propriedades.length} propriedade(s) monitorada(s)</div>
    </div>
    <h3>Análises laboratoriais (${f.analises.length})</h3>
    <table class="tab-ficha">
      <tr><th>Tipo</th><th>Coleta</th><th>Resultado</th><th>Fonte</th></tr>
      ${analises || "<tr><td colspan=4>sem análises</td></tr>"}
    </table>
    <h3>Eventos sanitários (${f.eventos.length})</h3>
    <ul class="lista">${eventos || "<li>nenhum</li>"}</ul>`;
}

carregar().catch((e) => {
  document.getElementById("ficha").innerHTML =
    `<div class="card" style="border-color:#c0392b;margin:20px">Erro: ${e.message}.<br>` +
    `<small>Rode <code>python -m ontology.materializar</code> (da raiz) para gerar ontologia.json.</small></div>`;
});
