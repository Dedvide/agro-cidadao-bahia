/* Apresentação Executiva guiada — Bahia Agro Inteligente.
   Cenas em tela cheia, narrativa para o secretário. Reusa os dados da demo. */

const cenas = [...document.querySelectorAll(".cena")];
let atual = 0;

async function init() {
  // carrega dados das cenas dinâmicas
  const [inst, laudos, chat] = await Promise.all([
    fetch("demo-institucional.json").then((r) => r.json()).catch(() => null),
    fetch("demo-laudos.json").then((r) => r.json()).catch(() => []),
    fetch("demo-chat.json").then((r) => r.json()).catch(() => []),
  ]);
  if (inst) capaNumeros(inst);
  if (laudos.length) cenaLaudo(laudos[0]);
  if (chat.length) cenaChat(chat);
  montarPontos();
  ir(0);

  document.getElementById("anterior").onclick = () => ir(atual - 1);
  document.getElementById("proximo").onclick = () => ir(atual + 1);
  document.getElementById("cheia").onclick = telaCheia;
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === "PageDown") ir(atual + 1);
    if (e.key === "ArrowLeft" || e.key === "PageUp") ir(atual - 1);
    if (e.key.toLowerCase() === "f") telaCheia();
  });
}

function capaNumeros(i) {
  const n = (x) => (typeof x === "number" ? x.toLocaleString("pt-BR") : x);
  document.getElementById("capa-numeros").innerHTML = [
    [n(i.analises), "análises/ano"], [n(i.laudos), "laudos emitidos"],
    [i.laboratorios, "laboratórios"], ["100%", "cobertura estadual"],
  ].map(([v, t]) => `<div class="n"><b>${v}</b><span>${t}</span></div>`).join("");
}

function cenaLaudo(l) {
  document.getElementById("ap-bruto").textContent = l.documento_bruto;
  const linhas = l.resultados.map((r) => {
    const cor = r.alerta ? "#c0392b" : "#1b7a3d";
    return `<tr><td>${r.rotulo}</td><td>${r.valor}</td>
      <td style="color:${cor};font-weight:700">${r.classe || "—"}</td></tr>`;
  }).join("");
  document.getElementById("ap-interpretado").innerHTML =
    `<div class="resumo-exec">${l.resumo}</div><table class="tab-ap">${linhas}</table>`;
}

function cenaChat(qa) {
  const escolhidos = [qa[0], qa.find((q) => q.tags.includes("hlb")) || qa[3] || qa[1]].filter(Boolean);
  document.getElementById("ap-chat").innerHTML = escolhidos.map((q) =>
    `<div class="bolha q">${q.pergunta}</div><div class="bolha a">${q.resposta}</div>`).join("");
}

function montarPontos() {
  document.getElementById("pontos").innerHTML =
    cenas.map((_, i) => `<div class="ponto" data-i="${i}"></div>`).join("");
  document.querySelectorAll(".ponto").forEach((p) => p.onclick = () => ir(+p.dataset.i));
}

function ir(i) {
  if (i < 0 || i >= cenas.length) return;
  atual = i;
  cenas.forEach((c, j) => c.classList.toggle("ativa", j === i));
  document.querySelectorAll(".ponto").forEach((p, j) => p.classList.toggle("on", j === i));
  // carrega iframes só quando a cena entra (performance)
  const ifr = cenas[i].querySelector("iframe[data-src]");
  if (ifr && !ifr.src) ifr.src = ifr.dataset.src;
}

function telaCheia() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
}

init();
