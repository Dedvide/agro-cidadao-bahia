/* Tela Integrações — catálogo do ecossistema (endpoints reais + exemplos).
   Inclui um teste de conexão AO VIVO com o IBGE (real) para confirmar a integração. */

const STATUS_LABEL = {
  api_publica: "API pública", convenio: "Requer convênio", parceria: "Parceria/Infra",
};
const STATUS_COR = { api_publica: "#1b7a3d", convenio: "#e67e22", parceria: "#2e86c1" };

async function carregar() {
  const d = await fetch("integracoes.json").then((r) => r.json());
  kpis(d.resumo);
  grupos(d.grupos);
}

function kpis(r) {
  const cards = [
    { v: r.total, t: "entes mapeados" },
    { v: r.api_publica, t: "API pública (autônomo)" },
    { v: r.convenio, t: "via convênio" },
    { v: r.parceria_infra, t: "parceria / infra" },
  ];
  document.getElementById("kpis").innerHTML = cards.map((c) =>
    `<div class="card"><div class="valor">${c.v}</div><div class="rotulo">${c.t}</div></div>`).join("");
}

function grupos(gs) {
  document.getElementById("grupos").innerHTML = gs.map((g) => `
    <div class="grupo-int">
      <h2>${g.esfera}</h2>
      <div class="int-grid">
        ${g.entes.map((e, i) => card(e, g.esfera + i)).join("")}
      </div>
    </div>`).join("");

  // liga os botões
  document.querySelectorAll("[data-exemplo]").forEach((b) =>
    b.addEventListener("click", () => {
      const box = document.getElementById(b.dataset.exemplo);
      box.style.display = box.style.display === "block" ? "none" : "block";
    }));
  const live = document.getElementById("btn-ibge");
  if (live) live.addEventListener("click", testarIBGE);
}

function card(e, id) {
  const cor = STATUS_COR[e.status] || "#7f8c8d";
  const liveBtn = e.live
    ? `<button id="btn-ibge" class="btn-int live">▶ Testar conexão ao vivo</button>
       <div id="ibge-res" class="exemplo"></div>`
    : "";
  return `<div class="int-card">
    <div class="int-top"><span class="int-ico">${e.icone}</span>
      <b>${e.nome}</b>
      <span class="pill" style="background:${cor}">${STATUS_LABEL[e.status]}</span></div>
    <div class="meta">${e.fornece}</div>
    <div class="int-mec">🔌 ${e.mecanismo} · <a href="${e.endpoint}" target="_blank">endpoint ↗</a></div>
    <button class="btn-int" data-exemplo="ex-${id}">ver exemplo de dado</button>
    <div id="ex-${id}" class="exemplo"><code>${e.exemplo}</code></div>
    ${liveBtn}
  </div>`;
}

async function testarIBGE() {
  const out = document.getElementById("ibge-res");
  out.style.display = "block";
  out.innerHTML = "<i>conectando ao IBGE…</i>";
  try {
    const url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/29/municipios";
    const r = await fetch(url);
    const arr = await r.json();
    out.innerHTML = `<b style="color:#1b7a3d">✓ conexão real OK</b> — ${arr.length} municípios da Bahia ` +
      `retornados pelo IBGE. Ex.: ${arr.slice(0, 4).map((m) => m.nome).join(", ")}…`;
  } catch (err) {
    out.innerHTML = `<b style="color:#e67e22">offline</b> — sem internet agora. ` +
      `Online, este botão traz os 417 municípios reais do IBGE (endpoint público, CORS aberto).`;
  }
}

carregar().catch((e) => {
  document.getElementById("grupos").innerHTML =
    `<div class="card" style="border-color:#c0392b;margin:24px">Erro: ${e.message}.</div>`;
});
