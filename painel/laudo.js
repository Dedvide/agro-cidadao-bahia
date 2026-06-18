/* Tela Laudos Inteligentes — documento → IA interpreta → decisão.
   Modo demo offline: lê demo-laudos.json (interpretações pré-computadas pelo motor real). */
let LAUDOS;

async function carregar() {
  const [laudos, inst] = await Promise.all([
    fetch("demo-laudos.json").then((r) => r.json()),
    fetch("demo-institucional.json").then((r) => r.json()).catch(() => null),
  ]);
  LAUDOS = laudos;
  if (inst) headline(inst);
  listar();
  selecionar(0);

  document.getElementById("arquivo").addEventListener("change", () => {
    // modo demo: qualquer upload mostra o 1º exemplo, sinalizando a simulação
    selecionar(0, true);
  });
}

function headline(i) {
  const n = (x) => (typeof x === "number" ? x.toLocaleString("pt-BR") : x);
  document.getElementById("headline").innerHTML =
    `<b>CETAB ${i.ano}:</b> ${n(i.analises)} análises · ${n(i.laudos)} laudos · ` +
    `${i.laboratorios} laboratórios · cobertura ${i.municipios} ` +
    `<span class="conf">(números a confirmar)</span>`;
}

function listar() {
  document.getElementById("amostras").innerHTML = LAUDOS.map((l, i) =>
    `<button class="amostra-btn" data-i="${i}"><b>${l.tipo}</b><br><span class="meta">${l.titulo}</span></button>`).join("");
  document.querySelectorAll(".amostra-btn").forEach((b) =>
    b.addEventListener("click", () => selecionar(+b.dataset.i)));
}

function selecionar(i, simulado) {
  const l = LAUDOS[i];
  document.querySelectorAll(".amostra-btn").forEach((b, j) => b.classList.toggle("sel", j === i));
  document.getElementById("bruto").textContent =
    (simulado ? "(modo demonstração — exibindo exemplo)\n\n" : "") + l.documento_bruto;

  const linhas = l.resultados.map((r) => {
    const cor = r.alerta ? "#c0392b" : "#1b7a3d";
    const rec = r.recomendacao ? `<div class="rec">→ ${r.recomendacao}</div>` : "";
    return `<tr><td>${r.rotulo}</td><td>${r.valor}</td>
      <td style="color:${cor};font-weight:600">${r.classe || "—"}${rec}</td></tr>`;
  }).join("");

  document.getElementById("resultado").innerHTML = `
    <div class="resumo-exec">${l.resumo}</div>
    <table class="tab-laudo">
      <tr><th>Parâmetro</th><th>Resultado</th><th>Interpretação / recomendação</th></tr>
      ${linhas}
    </table>
    <p class="hint">Transforma o laudo técnico em decisão que o produtor entende.</p>`;
}

carregar().catch((e) => {
  document.getElementById("resultado").innerHTML =
    `<div class="card" style="border-color:#c0392b">Erro: ${e.message}.<br>` +
    `<small>Rode <code>python gerar_demo_secretario.py</code> e sirva via <code>python -m http.server</code>.</small></div>`;
});
