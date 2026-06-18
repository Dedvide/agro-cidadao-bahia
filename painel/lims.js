/* Painel LIMS (protótipo) — leitura do fluxo coleta→laudo.
   Carrega lims.json: amostras, status, cadeia de custódia e laudo. */

const ROTULO_EIXO = {
  fertilidade_solo: "Fertilidade do solo", analise_agua: "Qualidade da água",
  residuos_agrotoxicos: "Resíduos", qualidade_alimentos: "Alimentos",
  diagnostico_molecular: "Diagnóstico molecular", monitoramento_pragas: "Pragas",
};
const ROTULO_STATUS = {
  cadastrada: "Cadastrada", coletada: "Coletada", recebida: "Recebida",
  em_analise: "Em análise", analisada: "Aguardando validação", validada: "Aprovada (emitir)",
  laudo_emitido: "Laudo emitido", entregue: "Entregue",
};
const COR_STATUS = {
  cadastrada: "#7f8c8d", coletada: "#7f8c8d", recebida: "#2e86c1", em_analise: "#e67e22",
  analisada: "#8e44ad", validada: "#16a085", laudo_emitido: "#1b7a3d", entregue: "#1b7a3d",
};
const nomeEixo = (c) => ROTULO_EIXO[c] || c;
const nomeStatus = (s) => ROTULO_STATUS[s] || s;
let DADOS;

async function carregar() {
  DADOS = await fetch("lims.json").then((r) => r.json());
  montarKPIs(DADOS.resumo);
  montarFiltro(DADOS);
  render("");
}

function montarKPIs(r) {
  const cards = [
    { v: r.total, t: "amostras" },
    { v: r.por_status["em_analise"] || 0, t: "em análise" },
    { v: r.fila_validacao, t: "aguardando validação", alerta: r.fila_validacao > 0 },
    { v: r.aguardando_emissao, t: "aprovadas p/ emitir" },
    { v: r.emitidos, t: "laudos emitidos" },
    { v: r.entregues, t: "entregues" },
  ];
  document.getElementById("kpis").innerHTML = cards.map((c) =>
    `<div class="card ${c.alerta ? "alerta" : ""}"><div class="valor">${c.v}</div>` +
    `<div class="rotulo">${c.t}</div></div>`).join("");
}

function montarFiltro(d) {
  const sel = document.getElementById("filtro-status");
  [...new Set(d.amostras.map((a) => a.status))].forEach((s) => {
    const o = document.createElement("option");
    o.value = s; o.textContent = nomeStatus(s);
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => render(sel.value));
}

function badge(status) {
  return `<span class="badge-status" style="background:${COR_STATUS[status] || "#7f8c8d"}">${nomeStatus(status)}</span>`;
}

function render(filtro) {
  const corpo = document.querySelector("#tabela-amostras tbody");
  const lista = filtro ? DADOS.amostras.filter((a) => a.status === filtro) : DADOS.amostras;
  corpo.innerHTML = lista.map((a, i) =>
    `<tr data-i="${DADOS.amostras.indexOf(a)}">
       <td><b>${a.protocolo}</b></td><td>${nomeEixo(a.categoria_analise)}</td>
       <td>${a.municipio || "—"}</td><td>${a.solicitante_nome || "—"}</td>
       <td>${badge(a.status)}</td>
     </tr>`).join("");
  corpo.querySelectorAll("tr").forEach((tr) =>
    tr.addEventListener("click", () => mostrarDetalhe(DADOS.amostras[+tr.dataset.i], tr)));
}

function mostrarDetalhe(a, tr) {
  document.querySelectorAll("#tabela-amostras tr").forEach((t) => t.classList.remove("sel"));
  if (tr) tr.classList.add("sel");

  const custodia = a.custodia.map((e) =>
    `<li><span class="ev">${nomeStatus(e.evento) || e.evento}</span>
       <span class="meta">${e.data} · ${e.responsavel}${e.observacao ? " · " + e.observacao : ""}</span></li>`
  ).join("");

  let laudoHtml = "<p class='hint'>Sem laudo ainda.</p>";
  if (a.laudo) {
    const l = a.laudo;
    const res = (l.resultados || []).map((r) =>
      `<tr><td>${r.rotulo}</td><td>${r.valor}</td>
         <td style="color:${r.alerta ? "#c0392b" : "#1b7a3d"};font-weight:600">${r.classe || "—"}</td></tr>`
    ).join("");
    const link = l.arquivo
      ? `<a class="btn" href="${l.arquivo}" target="_blank">Abrir laudo oficial ↗</a>` : "";
    const selo = l.codigo_verificacao
      ? `<div class="selo-mini">Cód. verificação: <b>${l.codigo_verificacao}</b></div>` : "";
    laudoHtml = `
      <div class="laudo-box">
        <div><b>${l.numero || "(laudo em preparação)"}</b> · status: ${l.status}</div>
        ${l.validado_por ? `<div class="meta">Validado por: ${l.validado_por}</div>` : ""}
        <table class="mini">${res}</table>
        ${selo}${link}
      </div>`;
  }

  document.getElementById("detalhe").innerHTML = `
    <h2>${a.protocolo} ${badge(a.status)}</h2>
    <div class="meta">${nomeEixo(a.categoria_analise)} · ${a.tipo_amostra} · ${a.municipio || "—"}</div>
    <div class="meta">Solicitante: ${a.solicitante_nome || "—"} (${a.solicitante_tipo || "—"}) ·
       coleta ${a.data_coleta || "—"} por ${a.coletor || "—"}</div>
    <h3>Laudo</h3>${laudoHtml}
    <h3>Cadeia de custódia</h3><ul class="timeline">${custodia}</ul>`;
}

carregar().catch((e) => {
  document.getElementById("kpis").innerHTML =
    `<div class="card" style="border-color:#c0392b">Erro: ${e.message}.<br>` +
    `<small>Rode <code>python gerar_lims_demo.py</code> e sirva via <code>python -m http.server</code>.</small></div>`;
});
